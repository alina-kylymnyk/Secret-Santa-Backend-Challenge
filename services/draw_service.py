import logging
import random
from typing import Dict, List

logger = logging.getLogger(__name__)


class DrawError(Exception):
    """Base exception for draw-related errors"""

    pass


class InsufficientParticipantError(DrawError):
    """Raised when there are not enough participants for a draw"""

    pass


class DrawService:
    """
    Service for performing Secret Santa draws.

    Implements a cyclic assignment algorithm that ensures:
    - Each participant gives to exactly one person
    - Each participant receives from exactly one person
    - No one gives to themselves
    - Perfect 1-to-1 mapping
    """

    MIN_PARTICIPANTS = 3

    @staticmethod
    def perform_draw(participants):
        # Validate input
        if not participants:
            raise InsufficientParticipantError("No participants provided")

        if len(participants) < DrawService.MIN_PARTICIPANTS:
            raise InsufficientParticipantError(
                f"Minimum {DrawService.MIN_PARTICIPANTS} participants required, "
                f"got {len(participants)}"
            )

        if len(participants) != len(set(participants)):
            raise DrawError("Duplicate participant names detected")

        logger.info(f"Starting draw for {len(participants)} participants")

        # Create a shuffled copy to ensure randomness
        shuffled = participants.copy()
        random.shuffle(shuffled)

        # Create cyclic assignment
        draw_result = DrawService._create_cyclic_assignment(shuffled)

        # Validate the result
        DrawService._validate_draw(draw_result, participants)

        logger.info(f"Draw completed successfully: {len(draw_result)} pairs created")
        return draw_result

    @staticmethod
    def _create_cyclic_assignment(participants):
        """
        Create a cyclic assignment where each person gives to the next
        """
        result = {}
        n = len(participants)

        for i in range(n):
            giver = participants[i]
            receiver = participants[(i + 1) % n]
            result[giver] = receiver

        return result

    @staticmethod
    def _validate_draw(draw_result, original_participants):
        """
        Validate that the draw result meets all requirements
        """

        participants_set = set(original_participants)

        # Check count
        if len(draw_result) != len(original_participants):
            raise DrawError(
                f"Draw result has {len(draw_result)} pairs, "
                f"expected {len(original_participants)}"
            )

        # Check for self-assignments
        for giver, receiver in draw_result.items():
            if giver == receiver:
                raise DrawError(f"Self-assignment detected: {giver} → {receiver}")

        # Check all participants are givers
        givers = set(draw_result.keys())
        if givers != participants_set:
            missing = participants_set - givers
            extra = givers - participants_set
            raise DrawError(f"Giver mismatch. Missing: {missing}, Extra: {extra}")

        # Check all participants are receivers
        receivers = set(draw_result.values())
        if receivers != participants_set:
            missing = participants_set - receivers
            extra = receivers - participants_set
            raise DrawError(f"Receiver mismatch. Missing: {missing}, Extra: {extra}")

        logger.debug("Draw validation passed")

    @staticmethod
    def verify_draw_properties(draw_result):
        """
        Verify mathematical properties of the draw
        """
        checks = {
            "no_self_assignment": True,
            "is_permutation": True,
            "is_cyclic": True,
        }

        # Check no self-assignments
        for giver, receiver in draw_result.items():
            if giver == receiver:
                checks["no_self_assignment"] = False
                break

        # Check if it's a valid permutation
        givers = set(draw_result.keys())
        receivers = set(draw_result.values())
        checks["is_permutation"] = givers == receivers

        # Check if it forms a cycle
        if draw_result:
            try:
                visited = set()
                current = next(iter(draw_result.keys()))
                start = current

                while current not in visited:
                    visited.add(current)
                    current = draw_result.get(current)

                    if current is None:
                        checks["is_cyclic"] = False
                        break

                # Should return to start and visit all participants
                checks["is_cyclic"] = current == start and len(visited) == len(
                    draw_result
                )
            except Exception:
                checks["is_cyclic"] = False

        return checks

class DrawStatistics:
    """
    Utility class for analyzing draw results and running simulations
    """

    @staticmethod
    def run_simulation(participants, iterations):
        """
        Run multiple draw simulations to verify algorithm correctness
        """
        service = DrawService()
        stats = {
            "total_iterations": iterations,
            "successful_draws": 0,
            "failed_draws": 0,
            "self_assignments_detected": 0,
            "unique_results": 0,
            "errors": [],
        }

        unique_results = set()

        for i in range(iterations):
            try:
                result = service.perform_draw(participants)
                stats["successful_draws"] += 1

                has_self_assignment = any(

                giver == receiver 
                for giver, receiver in result.items()
                )

                if has_self_assignment:
                    stats["self_assignments_detected"] += 1

                # Track unique results (as frozen set of tuples)
                result_tuple = tuple(sorted(result.items()))
                unique_results.add(result_tuple)

            except Exception as e:
                stats["failed_draws"] += 1
                stats["errors"].append(str(e))
                logger.error(f"Draw failed in iteration {i+1}: {e}")

        stats["unique_results"] = len(unique_results)

        logger.info(
            f"Simulation complete: {stats['successful_draws']}/{iterations} successful, "
            f"{stats['unique_results']} unique results"
        )

        return stats
    

    @staticmethod
    def analyze_draw_distribution(participants, iterations):
        """
        Analyze the distribution of assignments over multiple draws.
        """
        service = DrawService()

        distribution = {p: {other: 0 for other in participants if other != p} 
               for p in participants}
        
        for _ in range(iterations):
            try:
                result = service.perform_draw(participants)
                for giver, receiver in result.items():
                    distribution[giver][receiver] += 1
            except Exception as e:
                logger.error(f"Draw failed during distribution analysis: {e}")

        return distribution








        


