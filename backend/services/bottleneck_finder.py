"""
Bottleneck Finder Service
Implements greedy algorithm for finding top-K bottlenecks
"""

import logging
import json
from database_config import DatabaseConfig
from services.influence_models import InfluenceModels
from datetime import datetime

logger = logging.getLogger(__name__)


class BottleneckFinder:
    """Service for finding traffic bottlenecks"""

    def __init__(self):
        self.db_config = DatabaseConfig()
        self.influence_models = InfluenceModels()

    def get_db_connection(self):
        """Get database connection"""
        return self.db_config.get_db_connection()

    def find_top_k_bottlenecks(self, session_id, k=10, time_horizon=30, model_type='LIM', force_recalculate=False):
        """
        Find top K bottlenecks using greedy algorithm

        Args:
            session_id: UUID of the upload session
            k: Number of bottlenecks to find
            time_horizon: Time horizon in minutes
            model_type: Model type (LIM, LTM, SIR, SIS)
            force_recalculate: Force recalculation even if cached

        Returns:
            list: List of bottlenecks with rankings
        """
        conn = None
        cursor = None

        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()

            # Check cache (valid for 1 hour)
            if not force_recalculate:
                cursor.execute("""
                    SELECT
                        br.road_node_id,
                        rn.road_id,
                        rn.road_name,
                        br.rank_position,
                        br.benefit_score,
                        br.affected_roads_count,
                        ST_AsGeoJSON(ST_Centroid(rn.geometry)) as coordinates
                    FROM bottleneck_rankings br
                    JOIN road_nodes rn ON br.road_node_id = rn.id
                    WHERE br.session_id = %s
                      AND br.time_horizon_minutes = %s
                      AND br.calculation_timestamp > NOW() - INTERVAL '1 hour'
                    ORDER BY br.rank_position
                    LIMIT %s
                """, (session_id, time_horizon, k))

                cached_results = cursor.fetchall()

                if cached_results:
                    logger.info(f"Using cached bottleneck rankings for session {session_id}")

                    results = []
                    for row in cached_results:
                        coords = json.loads(row[6]) if row[6] else {'coordinates': [103.8198, 1.3521]}
                        results.append({
                            'road_node_id': row[0],
                            'road_id': row[1],
                            'road_name': row[2],
                            'rank': row[3],
                            'benefit_score': float(row[4]),
                            'affected_roads_count': row[5],
                            'coordinates': {
                                'lat': coords['coordinates'][1],
                                'lon': coords['coordinates'][0]
                            }
                        })

                    return {
                        'success': True,
                        'bottlenecks': results,
                        'cached': True
                    }

            # Calculate bottlenecks
            logger.info(f"Calculating top-{k} bottlenecks for session {session_id}")

            # Get all roads
            cursor.execute("""
                SELECT id, road_id, road_name, length_meters, capacity
                FROM road_nodes
                WHERE session_id = %s
            """, (session_id,))

            all_roads = {row[0]: {
                'road_id': row[1],
                'road_name': row[2],
                'length_meters': row[3] or 1000,
                'capacity': row[4] or 1000
            } for row in cursor.fetchall()}

            # Get current jammed roads as seeds
            seed_roads = self.influence_models.get_current_jammed_roads(session_id)

            if not seed_roads:
                # If no currently jammed roads, use random sample or all roads
                logger.warning(f"No currently jammed roads found for session {session_id}, using sample")
                seed_roads = list(all_roads.keys())[:5]  # Use first 5 roads as seeds

            # Greedy algorithm to find top-K bottlenecks
            selected_bottlenecks = []
            candidate_roads = set(all_roads.keys())

            for rank in range(1, k + 1):
                best_road = None
                best_benefit = 0

                # Try each candidate road
                for candidate_id in candidate_roads:
                    # Calculate benefit of fixing this road
                    benefit = self._calculate_benefit(
                        session_id,
                        seed_roads,
                        selected_bottlenecks + [candidate_id],
                        time_horizon,
                        model_type,
                        all_roads
                    )

                    if benefit > best_benefit:
                        best_benefit = benefit
                        best_road = candidate_id

                if best_road is None:
                    logger.warning(f"No more bottlenecks found at rank {rank}")
                    break

                # Add best road to selected bottlenecks
                selected_bottlenecks.append(best_road)
                candidate_roads.remove(best_road)

                logger.info(f"Rank {rank}: Road {all_roads[best_road]['road_name']} with benefit {best_benefit:.2f}")

            # Calculate affected roads for each bottleneck
            results = []
            for rank, road_id in enumerate(selected_bottlenecks, start=1):
                # Calculate affected roads count
                affected_count = self._count_affected_roads(
                    session_id,
                    seed_roads,
                    [road_id],
                    time_horizon,
                    model_type
                )

                # Get coordinates
                cursor.execute("""
                    SELECT ST_AsGeoJSON(ST_Centroid(geometry))
                    FROM road_nodes
                    WHERE id = %s
                """, (road_id,))

                coords_json = cursor.fetchone()[0]
                coords = json.loads(coords_json) if coords_json else {'coordinates': [103.8198, 1.3521]}

                # Calculate benefit score (normalized)
                benefit_score = self._calculate_benefit(
                    session_id,
                    seed_roads,
                    [road_id],
                    time_horizon,
                    model_type,
                    all_roads
                )

                results.append({
                    'road_node_id': road_id,
                    'road_id': all_roads[road_id]['road_id'],
                    'road_name': all_roads[road_id]['road_name'],
                    'rank': rank,
                    'benefit_score': benefit_score,
                    'affected_roads_count': affected_count,
                    'coordinates': {
                        'lat': coords['coordinates'][1],
                        'lon': coords['coordinates'][0]
                    }
                })

            # Cache results
            cursor.execute("""
                DELETE FROM bottleneck_rankings
                WHERE session_id = %s AND time_horizon_minutes = %s
            """, (session_id, time_horizon))

            for result in results:
                cursor.execute("""
                    INSERT INTO bottleneck_rankings (
                        road_node_id, rank_position, benefit_score, affected_roads_count,
                        calculation_timestamp, time_horizon_minutes, session_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    result['road_node_id'],
                    result['rank'],
                    result['benefit_score'],
                    result['affected_roads_count'],
                    datetime.now(),
                    time_horizon,
                    session_id
                ))

            conn.commit()

            logger.info(f"Successfully calculated and cached {len(results)} bottlenecks")

            return {
                'success': True,
                'bottlenecks': results,
                'cached': False
            }

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error finding bottlenecks: {str(e)}")
            raise e

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def _calculate_benefit(self, session_id, seed_roads, fixed_roads, time_horizon, model_type, all_roads):
        """
        Calculate benefit of fixing specific roads

        Args:
            session_id: Session ID
            seed_roads: Initially jammed roads
            fixed_roads: Roads to be fixed
            time_horizon: Time horizon in minutes
            model_type: Model type
            all_roads: Dictionary of all roads

        Returns:
            float: Benefit score
        """
        try:
            # Simulate baseline (no fixes)
            baseline_result = self.influence_models.predict_spread(
                session_id,
                seed_roads,
                time_horizon,
                model_type,
                num_simulations=50  # Reduced simulations for speed
            )

            baseline_jam_count = len(baseline_result.get('predictions', []))

            # Simulate with fixes (remove fixed roads from seeds)
            fixed_seed_roads = [r for r in seed_roads if r not in fixed_roads]

            if not fixed_seed_roads:
                # If all seeds are fixed, benefit is maximum
                return baseline_jam_count * 10

            fixed_result = self.influence_models.predict_spread(
                session_id,
                fixed_seed_roads,
                time_horizon,
                model_type,
                num_simulations=50
            )

            fixed_jam_count = len(fixed_result.get('predictions', []))

            # Benefit is reduction in jammed roads
            benefit = baseline_jam_count - fixed_jam_count

            # Weight by road importance (length * capacity)
            importance_weight = sum(
                all_roads[road_id]['length_meters'] * all_roads[road_id]['capacity']
                for road_id in fixed_roads
                if road_id in all_roads
            ) / 1000000  # Normalize

            return benefit + importance_weight

        except Exception as e:
            logger.warning(f"Error calculating benefit: {str(e)}")
            return 0.0

    def _count_affected_roads(self, session_id, seed_roads, fixed_roads, time_horizon, model_type):
        """
        Count roads affected by fixing specific bottlenecks

        Args:
            session_id: Session ID
            seed_roads: Initially jammed roads
            fixed_roads: Roads to be fixed
            time_horizon: Time horizon
            model_type: Model type

        Returns:
            int: Number of affected roads
        """
        try:
            # Simulate baseline
            baseline_result = self.influence_models.predict_spread(
                session_id,
                seed_roads,
                time_horizon,
                model_type,
                num_simulations=50
            )

            baseline_roads = set(
                pred['road_node_id']
                for pred in baseline_result.get('predictions', [])
                if pred['jam_probability'] >= 0.1
            )

            # Simulate with fixes
            fixed_seed_roads = [r for r in seed_roads if r not in fixed_roads]

            if not fixed_seed_roads:
                return len(baseline_roads)

            fixed_result = self.influence_models.predict_spread(
                session_id,
                fixed_seed_roads,
                time_horizon,
                model_type,
                num_simulations=50
            )

            fixed_roads_set = set(
                pred['road_node_id']
                for pred in fixed_result.get('predictions', [])
                if pred['jam_probability'] >= 0.1
            )

            # Affected roads are those that no longer jam
            affected_roads = baseline_roads - fixed_roads_set

            return len(affected_roads)

        except Exception as e:
            logger.warning(f"Error counting affected roads: {str(e)}")
            return 0

    def what_if_analysis(self, session_id, fixed_roads, time_horizon, model_type='LIM'):
        """
        Perform what-if analysis for fixing specific roads

        Args:
            session_id: Session ID
            fixed_roads: List of road IDs to fix
            time_horizon: Time horizon in minutes
            model_type: Model type

        Returns:
            dict: Analysis results
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

            all_roads = {row[0]: {'road_id': row[1], 'road_name': row[2]} for row in cursor.fetchall()}

            # Get current jammed roads
            seed_roads = self.influence_models.get_current_jammed_roads(session_id)

            if not seed_roads:
                seed_roads = list(all_roads.keys())[:5]

            # Simulate baseline
            baseline_result = self.influence_models.predict_spread(
                session_id,
                seed_roads,
                time_horizon,
                model_type
            )

            # Simulate with fixes
            fixed_seed_roads = [r for r in seed_roads if r not in fixed_roads]

            fixed_result = self.influence_models.predict_spread(
                session_id,
                fixed_seed_roads,
                time_horizon,
                model_type
            )

            # Calculate differences
            baseline_jams = {pred['road_node_id']: pred['jam_probability']
                           for pred in baseline_result.get('predictions', [])}
            fixed_jams = {pred['road_node_id']: pred['jam_probability']
                        for pred in fixed_result.get('predictions', [])}

            affected_roads = []
            for road_id in baseline_jams:
                baseline_prob = baseline_jams.get(road_id, 0)
                fixed_prob = fixed_jams.get(road_id, 0)
                reduction = baseline_prob - fixed_prob

                if reduction > 0.1:  # Significant reduction
                    affected_roads.append({
                        'road_node_id': road_id,
                        'road_name': all_roads[road_id]['road_name'],
                        'baseline_probability': baseline_prob,
                        'fixed_probability': fixed_prob,
                        'reduction': reduction
                    })

            affected_roads.sort(key=lambda x: x['reduction'], reverse=True)

            total_benefit = sum(road['reduction'] for road in affected_roads)

            return {
                'success': True,
                'fixed_roads': [all_roads[rid]['road_name'] for rid in fixed_roads if rid in all_roads],
                'total_benefit': total_benefit,
                'affected_roads': affected_roads,
                'baseline_jam_count': len([p for p in baseline_result.get('predictions', []) if p['jam_probability'] >= 0.5]),
                'fixed_jam_count': len([p for p in fixed_result.get('predictions', []) if p['jam_probability'] >= 0.5])
            }

        except Exception as e:
            logger.error(f"Error in what-if analysis: {str(e)}")
            raise e

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
