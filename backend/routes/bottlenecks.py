"""
Bottleneck Routes
Handles bottleneck analysis and predictions
"""

from flask import Blueprint, request, jsonify
import logging
import os
import sys

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.bottleneck_finder import BottleneckFinder
from services.influence_models import InfluenceModels
from database_config import DatabaseConfig

logger = logging.getLogger(__name__)

# Create blueprint
bottlenecks_bp = Blueprint('bottlenecks', __name__, url_prefix='/api/bottlenecks')


def get_db_connection():
    """Get database connection"""
    db_config = DatabaseConfig()
    return db_config.get_db_connection()


@bottlenecks_bp.route('/run-model', methods=['POST'])
def run_model():
    """
    Run bottleneck analysis model on uploaded data
    """
    try:
        data = request.get_json()

        session_id = data.get('session_id')
        k = data.get('k', 10)
        time_horizon = data.get('time_horizon', 30)
        model_type = data.get('model_type', 'LIM')

        if not session_id:
            return jsonify({
                'success': False,
                'error': 'session_id is required'
            }), 400

        # Validate session status
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT status
            FROM upload_sessions
            WHERE session_id = %s
        """, (session_id,))

        session = cursor.fetchone()

        if not session:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404

        status = session[0]

        if status != 'ready':
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': f'Session is not ready. Current status: {status}'
            }), 400

        # Check if the selected algorithm is active
        cursor.execute("""
            SELECT is_active, name 
            FROM algorithms 
            WHERE model_type = %s
        """, (model_type,))
        
        algorithm_result = cursor.fetchone()
        
        if algorithm_result:
            is_active = algorithm_result[0]
            algo_name = algorithm_result[1]
            if not is_active:
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'error': f'Algorithm "{algo_name}" ({model_type}) is currently suspended and cannot be used.'
                }), 403

        cursor.close()
        conn.close()

        logger.info(f"Running bottleneck model for session {session_id}")

        # Initialize services
        influence_models = InfluenceModels()
        bottleneck_finder = BottleneckFinder()

        # Check if influence probabilities are learned
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM influence_probabilities
            WHERE session_id = %s
        """, (session_id,))

        prob_count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        # Learn influence probabilities if not already done
        if prob_count == 0:
            logger.info(f"Learning influence probabilities for session {session_id}")
            influence_models.learn_influence_probabilities(
                session_id,
                time_horizons=[5, 15, 30],
                model_type=model_type
            )
            logger.info(f"Successfully learned influence probabilities")

        # Find top-K bottlenecks
        logger.info(f"Finding top-{k} bottlenecks")
        result = bottleneck_finder.find_top_k_bottlenecks(
            session_id=session_id,
            k=k,
            time_horizon=time_horizon,
            model_type=model_type,
            force_recalculate=True
        )

        logger.info(f"Successfully found {len(result.get('bottlenecks', []))} bottlenecks")

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error running bottleneck model: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to run model: {str(e)}'
        }), 500


@bottlenecks_bp.route('/top-k', methods=['GET'])
def get_top_bottlenecks():
    """
    Get top K bottlenecks (cached or calculate new)
    """
    try:
        k = int(request.args.get('k', 10))
        time_horizon = int(request.args.get('time_horizon', 30))
        model_type = request.args.get('model_type', 'LIM')
        force_recalculate = request.args.get('force', 'false').lower() == 'true'

        # Get active session
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT session_id
            FROM upload_sessions
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """)

        session = cursor.fetchone()

        if not session:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'No active session found'
            }), 404

        session_id = str(session[0])

        cursor.close()
        conn.close()

        # Find bottlenecks
        bottleneck_finder = BottleneckFinder()
        result = bottleneck_finder.find_top_k_bottlenecks(
            session_id=session_id,
            k=k,
            time_horizon=time_horizon,
            model_type=model_type,
            force_recalculate=force_recalculate
        )

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error getting top bottlenecks: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get bottlenecks: {str(e)}'
        }), 500


@bottlenecks_bp.route('/calculate', methods=['POST'])
def calculate_bottlenecks():
    """
    Trigger bottleneck calculation
    """
    try:
        data = request.get_json()

        k = data.get('k', 10)
        time_horizon = data.get('time_horizon', 30)
        model_type = data.get('model_type', 'LIM')

        # Get active session
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT session_id
            FROM upload_sessions
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """)

        session = cursor.fetchone()

        if not session:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'No active session found'
            }), 404

        session_id = str(session[0])

        cursor.close()
        conn.close()

        # Calculate bottlenecks
        bottleneck_finder = BottleneckFinder()
        result = bottleneck_finder.find_top_k_bottlenecks(
            session_id=session_id,
            k=k,
            time_horizon=time_horizon,
            model_type=model_type,
            force_recalculate=True
        )

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error calculating bottlenecks: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to calculate bottlenecks: {str(e)}'
        }), 500


@bottlenecks_bp.route('/what-if', methods=['POST'])
def what_if_analysis():
    """
    Perform what-if analysis for fixing specific roads
    """
    try:
        data = request.get_json()

        fixed_road_ids = data.get('fixed_roads', [])
        time_horizon = data.get('time_horizon', 30)
        model_type = data.get('model_type', 'LIM')

        if not fixed_road_ids:
            return jsonify({
                'success': False,
                'error': 'fixed_roads is required'
            }), 400

        # Get active session
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT session_id
            FROM upload_sessions
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """)

        session = cursor.fetchone()

        if not session:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'No active session found'
            }), 404

        session_id = str(session[0])

        cursor.close()
        conn.close()

        # Perform what-if analysis
        bottleneck_finder = BottleneckFinder()
        result = bottleneck_finder.what_if_analysis(
            session_id=session_id,
            fixed_roads=fixed_road_ids,
            time_horizon=time_horizon,
            model_type=model_type
        )

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error in what-if analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'What-if analysis failed: {str(e)}'
        }), 500


@bottlenecks_bp.route('/learn-influence', methods=['POST'])
def learn_influence():
    """
    Trigger learning of influence probabilities from historical data
    """
    try:
        data = request.get_json()

        time_horizons = data.get('time_horizons', [5, 15, 30])
        model_type = data.get('model_type', 'LIM')

        # Get active session
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT session_id
            FROM upload_sessions
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """)

        session = cursor.fetchone()

        if not session:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'No active session found'
            }), 404

        session_id = str(session[0])

        cursor.close()
        conn.close()

        # Learn influence probabilities
        influence_models = InfluenceModels()
        result = influence_models.learn_influence_probabilities(
            session_id=session_id,
            time_horizons=time_horizons,
            model_type=model_type
        )

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error learning influence probabilities: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to learn influence probabilities: {str(e)}'
        }), 500


@bottlenecks_bp.route('/influence-flows', methods=['GET'])
def get_influence_flows():
    """
    Get influence flow connections between roads for visualization
    Returns edges with coordinates to draw animated lines on the map
    """
    try:
        time_horizon = int(request.args.get('time_horizon', 30))
        min_probability = float(request.args.get('min_probability', 0.3))

        # Get active session
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT session_id
            FROM upload_sessions
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """)

        session = cursor.fetchone()

        if not session:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'No active session found'
            }), 404

        session_id = str(session[0])

        # Get influence flows with coordinates
        cursor.execute("""
            SELECT
                ip.from_road_node_id,
                ip.to_road_node_id,
                ip.probability,
                ip.confidence,
                rn_from.road_name as from_road_name,
                rn_to.road_name as to_road_name,
                ST_AsGeoJSON(ST_Centroid(rn_from.geometry)) as from_coords,
                ST_AsGeoJSON(ST_Centroid(rn_to.geometry)) as to_coords
            FROM influence_probabilities ip
            JOIN road_nodes rn_from ON ip.from_road_node_id = rn_from.id
            JOIN road_nodes rn_to ON ip.to_road_node_id = rn_to.id
            WHERE ip.session_id = %s
              AND ip.time_horizon_minutes = %s
              AND ip.probability >= %s
            ORDER BY ip.probability DESC
            LIMIT 100
        """, (session_id, time_horizon, min_probability))

        flows = []
        for row in cursor.fetchall():
            import json
            from_coords = json.loads(row[6]) if row[6] else None
            to_coords = json.loads(row[7]) if row[7] else None

            if from_coords and to_coords:
                flows.append({
                    'from_road_id': row[0],
                    'to_road_id': row[1],
                    'probability': float(row[2]),
                    'confidence': row[3],
                    'from_road_name': row[4],
                    'to_road_name': row[5],
                    'from_coords': {
                        'lat': from_coords['coordinates'][1],
                        'lon': from_coords['coordinates'][0]
                    },
                    'to_coords': {
                        'lat': to_coords['coordinates'][1],
                        'lon': to_coords['coordinates'][0]
                    }
                })

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'flows': flows,
            'count': len(flows)
        }), 200

    except Exception as e:
        logger.error(f"Error getting influence flows: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get influence flows: {str(e)}'
        }), 500


@bottlenecks_bp.route('/bottleneck-impacts', methods=['GET'])
def get_bottleneck_impacts():
    """
    Get the impact connections from bottlenecks to affected roads
    Returns edges showing which roads are affected by each bottleneck
    """
    try:
        time_horizon = int(request.args.get('time_horizon', 30))
        bottleneck_id = request.args.get('bottleneck_id')

        # Get active session
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT session_id
            FROM upload_sessions
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1
        """)

        session = cursor.fetchone()

        if not session:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'No active session found'
            }), 404

        session_id = str(session[0])

        # Get bottleneck rankings with their affected roads
        if bottleneck_id:
            # Get impacts for specific bottleneck
            cursor.execute("""
                SELECT
                    br.road_node_id as bottleneck_id,
                    rn_bn.road_name as bottleneck_name,
                    ST_AsGeoJSON(ST_Centroid(rn_bn.geometry)) as bottleneck_coords,
                    ip.to_road_node_id as affected_id,
                    rn_aff.road_name as affected_name,
                    ST_AsGeoJSON(ST_Centroid(rn_aff.geometry)) as affected_coords,
                    ip.probability
                FROM bottleneck_rankings br
                JOIN road_nodes rn_bn ON br.road_node_id = rn_bn.id
                JOIN influence_probabilities ip ON ip.from_road_node_id = br.road_node_id
                JOIN road_nodes rn_aff ON ip.to_road_node_id = rn_aff.id
                WHERE br.session_id = %s
                  AND br.time_horizon_minutes = %s
                  AND br.road_node_id = %s
                  AND ip.session_id = %s
                  AND ip.time_horizon_minutes = %s
                  AND ip.probability >= 0.2
                ORDER BY ip.probability DESC
                LIMIT 20
            """, (session_id, time_horizon, bottleneck_id, session_id, time_horizon))
        else:
            # Get top impacts from all bottlenecks
            cursor.execute("""
                SELECT
                    br.road_node_id as bottleneck_id,
                    rn_bn.road_name as bottleneck_name,
                    ST_AsGeoJSON(ST_Centroid(rn_bn.geometry)) as bottleneck_coords,
                    ip.to_road_node_id as affected_id,
                    rn_aff.road_name as affected_name,
                    ST_AsGeoJSON(ST_Centroid(rn_aff.geometry)) as affected_coords,
                    ip.probability,
                    br.rank_position
                FROM bottleneck_rankings br
                JOIN road_nodes rn_bn ON br.road_node_id = rn_bn.id
                JOIN influence_probabilities ip ON ip.from_road_node_id = br.road_node_id
                JOIN road_nodes rn_aff ON ip.to_road_node_id = rn_aff.id
                WHERE br.session_id = %s
                  AND br.time_horizon_minutes = %s
                  AND ip.session_id = %s
                  AND ip.time_horizon_minutes = %s
                  AND ip.probability >= 0.3
                ORDER BY br.rank_position ASC, ip.probability DESC
                LIMIT 50
            """, (session_id, time_horizon, session_id, time_horizon))

        impacts = []
        for row in cursor.fetchall():
            import json
            bn_coords = json.loads(row[2]) if row[2] else None
            aff_coords = json.loads(row[5]) if row[5] else None

            if bn_coords and aff_coords:
                impacts.append({
                    'bottleneck_id': row[0],
                    'bottleneck_name': row[1],
                    'bottleneck_coords': {
                        'lat': bn_coords['coordinates'][1],
                        'lon': bn_coords['coordinates'][0]
                    },
                    'affected_id': row[3],
                    'affected_name': row[4],
                    'affected_coords': {
                        'lat': aff_coords['coordinates'][1],
                        'lon': aff_coords['coordinates'][0]
                    },
                    'probability': float(row[6])
                })

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'impacts': impacts,
            'count': len(impacts)
        }), 200

    except Exception as e:
        logger.error(f"Error getting bottleneck impacts: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get bottleneck impacts: {str(e)}'
        }), 500
