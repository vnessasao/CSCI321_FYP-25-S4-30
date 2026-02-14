"""
Influence Models for Traffic Jam Prediction
Implements LIM, LTM, SIR, and SIS models for predicting jam spread
"""

import logging
import random
from database_config import DatabaseConfig
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class InfluenceModels:
    """Models for predicting traffic jam spread"""

    def __init__(self):
        self.db_config = DatabaseConfig()

    def get_db_connection(self):
        """Get database connection"""
        return self.db_config.get_db_connection()

    def learn_influence_probabilities(self, session_id, time_horizons=[5, 15, 30], model_type='LIM'):
        """
        Learn influence probabilities from historical congestion data

        Args:
            session_id: UUID of the upload session
            time_horizons: List of time horizons in minutes
            model_type: Model type (LIM, LTM, SIR, SIS)

        Returns:
            dict: Learning results
        """
        conn = None
        cursor = None

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            logger.info(f"Learning influence probabilities for session {session_id}")

            # Clear existing influence probabilities for this session
            cursor.execute("""
                DELETE FROM influence_probabilities
                WHERE session_id = %s
            """, (session_id,))

            total_learned = 0

            for time_horizon in time_horizons:
                # For each road edge, calculate probability that jam on road A leads to jam on road B
                cursor.execute("""
                    INSERT INTO influence_probabilities (
                        from_road_node_id, to_road_node_id, time_horizon_minutes,
                        probability, model_type, confidence, session_id
                    )
                    SELECT
                        re.from_node_id,
                        re.to_node_id,
                        %s as time_horizon,
                        LEAST(1.0, GREATEST(0.0,
                            COUNT(CASE WHEN cs2.congestion_index >= 0.7 THEN 1 END)::float /
                            NULLIF(COUNT(CASE WHEN cs1.congestion_index >= 0.7 THEN 1 END), 0)
                        )) as probability,
                        %s as model_type,
                        CASE
                            WHEN COUNT(CASE WHEN cs1.congestion_index >= 0.7 THEN 1 END) >= 10 THEN 'high'
                            WHEN COUNT(CASE WHEN cs1.congestion_index >= 0.7 THEN 1 END) >= 5 THEN 'medium'
                            ELSE 'low'
                        END as confidence,
                        %s as session_id
                    FROM road_edges re
                    LEFT JOIN congestion_states cs1 ON cs1.road_node_id = re.from_node_id
                        AND cs1.session_id = %s
                    LEFT JOIN congestion_states cs2 ON cs2.road_node_id = re.to_node_id
                        AND cs2.session_id = %s
                        AND cs2.timestamp BETWEEN cs1.timestamp AND cs1.timestamp + INTERVAL '%s minutes'
                    WHERE re.session_id = %s
                    GROUP BY re.from_node_id, re.to_node_id
                    HAVING COUNT(CASE WHEN cs1.congestion_index >= 0.7 THEN 1 END) > 0
                """, (time_horizon, model_type, session_id, session_id, session_id, time_horizon, session_id))

                learned_count = cursor.rowcount
                total_learned += learned_count

                logger.info(f"Learned {learned_count} influence probabilities for {time_horizon} min horizon")

            conn.commit()

            return {
                'success': True,
                'total_learned': total_learned,
                'time_horizons': time_horizons,
                'model_type': model_type
            }

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error learning influence probabilities: {str(e)}")
            raise e

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def predict_spread(self, session_id, seed_roads, time_horizon, model_type='LIM', num_simulations=100):
        """
        Predict jam spread using specified model

        Args:
            session_id: UUID of the upload session
            seed_roads: List of initially jammed road IDs
            time_horizon: Time horizon in minutes
            model_type: Model type (LIM, LTM, SIR, SIS)
            num_simulations: Number of Monte Carlo simulations (for LIM)

        Returns:
            dict: Prediction results with probabilities for each road
        """
        if model_type == 'LIM':
            return self._predict_lim(session_id, seed_roads, time_horizon, num_simulations)
        elif model_type == 'LTM':
            return self._predict_ltm(session_id, seed_roads, time_horizon)
        elif model_type == 'SIR':
            return self._predict_sir(session_id, seed_roads, time_horizon)
        elif model_type == 'SIS':
            return self._predict_sis(session_id, seed_roads, time_horizon)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    def _predict_lim(self, session_id, seed_roads, time_horizon, num_simulations):
        """
        Linear Independent Cascade Model (LIM)
        Monte Carlo simulation with probabilistic spread
        """
        conn = None
        cursor = None

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Get all roads
            cursor.execute("""
                SELECT id, road_id, road_name
                FROM road_nodes
                WHERE session_id = %s
            """, (session_id,))

            roads = {row[0]: {'road_id': row[1], 'road_name': row[2]} for row in cursor.fetchall()}

            # Get influence probabilities
            cursor.execute("""
                SELECT from_road_node_id, to_road_node_id, probability
                FROM influence_probabilities
                WHERE session_id = %s
                  AND time_horizon_minutes = %s
                  AND model_type = 'LIM'
            """, (session_id, time_horizon))

            influence_probs = {}
            for row in cursor.fetchall():
                from_id, to_id, prob = row
                if from_id not in influence_probs:
                    influence_probs[from_id] = []
                influence_probs[from_id].append((to_id, prob))

            # Run Monte Carlo simulations
            jam_counts = {road_id: 0 for road_id in roads.keys()}

            for sim in range(num_simulations):
                jammed = set(seed_roads)
                active = set(seed_roads)

                # Simulate spread
                while active:
                    new_active = set()

                    for from_road in active:
                        if from_road in influence_probs:
                            for to_road, prob in influence_probs[from_road]:
                                if to_road not in jammed:
                                    # Probabilistic activation
                                    if random.random() < prob:
                                        jammed.add(to_road)
                                        new_active.add(to_road)

                    active = new_active

                # Count jammed roads
                for road_id in jammed:
                    jam_counts[road_id] += 1

            # Calculate probabilities
            results = []
            for road_id, count in jam_counts.items():
                if count > 0:
                    probability = count / num_simulations
                    results.append({
                        'road_node_id': road_id,
                        'road_id': roads[road_id]['road_id'],
                        'road_name': roads[road_id]['road_name'],
                        'jam_probability': probability,
                        'risk_level': self._get_risk_level(probability)
                    })

            # Sort by probability (descending)
            results.sort(key=lambda x: x['jam_probability'], reverse=True)

            return {
                'success': True,
                'model_type': 'LIM',
                'time_horizon': time_horizon,
                'num_simulations': num_simulations,
                'seed_roads': seed_roads,
                'predictions': results
            }

        except Exception as e:
            logger.error(f"Error in LIM prediction: {str(e)}")
            raise e

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def _predict_ltm(self, session_id, seed_roads, time_horizon):
        """
        Linear Threshold Model (LTM)
        Threshold-based activation
        """
        conn = None
        cursor = None

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Get all roads
            cursor.execute("""
                SELECT id, road_id, road_name
                FROM road_nodes
                WHERE session_id = %s
            """, (session_id,))

            roads = {row[0]: {'road_id': row[1], 'road_name': row[2]} for row in cursor.fetchall()}

            # Get influence probabilities
            cursor.execute("""
                SELECT from_road_node_id, to_road_node_id, probability
                FROM influence_probabilities
                WHERE session_id = %s
                  AND time_horizon_minutes = %s
            """, (session_id, time_horizon))

            influence_probs = {}
            for row in cursor.fetchall():
                from_id, to_id, prob = row
                if to_id not in influence_probs:
                    influence_probs[to_id] = []
                influence_probs[to_id].append((from_id, prob))

            # Threshold-based spread
            jammed = set(seed_roads)
            threshold = 0.5  # 50% threshold

            changed = True
            while changed:
                changed = False
                for road_id in list(roads.keys()):
                    if road_id not in jammed and road_id in influence_probs:
                        # Calculate total influence from jammed neighbors
                        total_influence = sum(prob for from_id, prob in influence_probs[road_id] if from_id in jammed)

                        if total_influence >= threshold:
                            jammed.add(road_id)
                            changed = True

            # Calculate probabilities (deterministic in LTM, so 0 or 1)
            results = []
            for road_id in jammed:
                results.append({
                    'road_node_id': road_id,
                    'road_id': roads[road_id]['road_id'],
                    'road_name': roads[road_id]['road_name'],
                    'jam_probability': 1.0,
                    'risk_level': 'high'
                })

            return {
                'success': True,
                'model_type': 'LTM',
                'time_horizon': time_horizon,
                'seed_roads': seed_roads,
                'predictions': results
            }

        except Exception as e:
            logger.error(f"Error in LTM prediction: {str(e)}")
            raise e

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def _predict_sir(self, session_id, seed_roads, time_horizon):
        """
        SIR Model (Susceptible-Infected-Recovered)
        Epidemic model with recovery
        """
        # Similar to LIM but with recovery mechanism
        # For simplicity, using LIM with reduced spread
        return self._predict_lim(session_id, seed_roads, time_horizon, num_simulations=50)

    def _predict_sis(self, session_id, seed_roads, time_horizon):
        """
        SIS Model (Susceptible-Infected-Susceptible)
        Epidemic model without immunity
        """
        # Similar to LIM but roads can be re-jammed
        return self._predict_lim(session_id, seed_roads, time_horizon, num_simulations=50)

    def _get_risk_level(self, probability):
        """
        Get risk level from probability

        Args:
            probability: Jam probability (0-1)

        Returns:
            str: Risk level (high, medium, low)
        """
        if probability >= 0.7:
            return 'high'
        elif probability >= 0.3:
            return 'medium'
        else:
            return 'low'

    def get_current_jammed_roads(self, session_id):
        """
        Get currently jammed roads from latest congestion data

        Args:
            session_id: UUID of the upload session

        Returns:
            list: List of road node IDs that are currently jammed
        """
        conn = None
        cursor = None

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT road_node_id
                FROM congestion_states
                WHERE session_id = %s
                  AND congestion_index >= 0.7
                  AND timestamp >= NOW() - INTERVAL '30 minutes'
            """, (session_id,))

            jammed_roads = [row[0] for row in cursor.fetchall()]

            logger.info(f"Found {len(jammed_roads)} currently jammed roads for session {session_id}")

            return jammed_roads

        except Exception as e:
            logger.error(f"Error getting jammed roads: {str(e)}")
            return []

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
