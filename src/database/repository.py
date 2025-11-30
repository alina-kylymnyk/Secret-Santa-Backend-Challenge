import logging
from datetime import datetime
from typing import Dict, List

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import DrawResult, Game, Participant

logger = logging.getLogger(__name__)


class GameRepository:
    """Handles all database operations separately from the main app logic"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_game(self, game_code, creator_chat_id, auto_purge_at=None):
        """
        Create a new Secret Santa game
        """
        game = Game(
            game_code=game_code,
            creator_chat_id=creator_chat_id,
            auto_purge_at=auto_purge_at,
        )
        self.session.add(game)
        await self.session.flush()  # Ensure data is written to DB
        await self.session.refresh(game)  # Refresh to get ID from DB

        logger.info(f"Created game: {game.game_code} (ID: {game.id})")

        # Verify game was created
        verification = await self.get_game_by_code(game_code)
        if verification:
            logger.info(f"Game creation verified in DB: {game_code}")
        else:
            logger.error(f"Game creation FAILED verification: {game_code}")

        return game

    async def get_game_by_code(self, game_code):
        """
        Retrieve a game by its unique code
        """
        stmt = select(Game).where(Game.game_code == game_code)
        result = await self.session.execute(stmt)
        game = result.scalar_one_or_none()

        if game:
            logger.debug(f"Found game: {game_code}")
        else:
            logger.debug(f"Game not found: {game_code}")

        return game

    async def get_game_by_id(self, game_id):
        """
        Retrieve a game by its ID.
        """
        stmt = select(Game).where(Game.id == game_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_participant(self, game_id, name):
        """
        Add a participant to a game.
        """
        participant = Participant(
            game_id=game_id,
            name=name,
        )
        self.session.add(participant)
        try:
            await self.session.flush()
            await self.session.refresh(participant)
            logger.info(f"Added participant '{name}' to game ID {game_id}")
            return participant
        except Exception as e:
            logger.error(f"Failed to add participant '{name}': {e}")
            raise

    async def get_participants(self, game_id):
        """
        Get all participants in a game.
        """
        stmt = (
            select(Participant)
            .where(Participant.game_id == game_id)
            .order_by(Participant.joined_at)
        )
        result = await self.session.execute(stmt)
        participants = list(result.scalars().all())

        logger.debug(
            f"Retrieved {len(participants)} participants for game ID {game_id}"
        )
        return participants

    async def participant_exists(self, game_id, name):
        """
        Check if a participant with given name exists in the game
        """
        stmt = select(Participant).where(
            Participant.game_id == game_id, Participant.name == name
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def lock_game(self, game_id):
        """
        Lock a game to prevent new participants from joining
        """
        stmt = update(Game).where(Game.id == game_id).values(is_locked=True)
        await self.session.execute(stmt)
        logger.info(f"Locked game ID {game_id}")

    async def mark_game_as_drawn(self, game_id):
        """
        Mark a game as drawn
        """
        stmt = update(Game).where(Game.id == game_id).values(is_drawn=True)
        await self.session.execute(stmt)
        logger.info(f"Marked game ID {game_id} as drawn")

    async def save_draw_results(self, game_id, results):
        """
        Save Secret Santa draw results
        """
        draw_results = []

        for giver_name, receiver_name in results.items():
            draw_result = DrawResult(
                game_id=game_id,
                giver_name=giver_name,
                receiver_name=receiver_name,
            )
            self.session.add(draw_result)
            draw_results.append(draw_result)

        await self.session.flush()

        await self.mark_game_as_drawn(game_id)

        logger.info(f"Saved {len(draw_results)} draw results for game ID {game_id}")
        return draw_results

    async def get_draw_results(self, game_id):
        """
        Get all draw results for a game
        """
        stmt = (
            select(DrawResult)
            .where(DrawResult.game_id == game_id)
            .order_by(DrawResult.giver_name)
        )
        result = await self.session.execute(stmt)
        draw_results = list(result.scalars().all())

        logger.debug(
            f"Retrieved {len(draw_results)} draw results for game ID {game_id}"
        )
        return draw_results

    async def delete_game(self, game_id):
        """
        Delete a game and all related data (participants, draw results)
        """
        # First delete participants
        stmt_participants = delete(Participant).where(Participant.game_id == game_id)
        await self.session.execute(stmt_participants)

        # Then delete draw results
        stmt_draw_results = delete(DrawResult).where(DrawResult.game_id == game_id)
        await self.session.execute(stmt_draw_results)

        # Finally delete the game itself
        stmt = delete(Game).where(Game.id == game_id)
        result = await self.session.execute(stmt)

        deleted = result.rowcount > 0

        if deleted:
            logger.info(f"Deleted game ID {game_id} and all related data")
        else:
            logger.warning(f"Game ID {game_id} not found for deletion")

        return deleted
    
    async def get_expired_games(self, current_time):
        """
        Get all games that have passed their auto-purge date
        """
        if current_time is None:
            current_time = datetime.utcnow()

        stmt = (
            select(Game)
            .where(
                Game.auto_purge_at.isnot(None),
                Game.auto_purge_at <= current_time
            )
        )
        result = await self.session.execute(stmt)
        expired_games = list(result.scalars().all())

        logger.debug(f"Found {len(expired_games)} expired games")
        return expired_games
    
    async def get_game_with_participants(self, game_code):
        """
        Get a game with all its participants eagerly loaded
        """
        stmt = (
            select(Game)
            .where(Game.game_code == game_code)
            .options(selectinload(Game.participants))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_game_stats(self, game_id):
        """
        Get statistics for a game.
        """
        participants = await self.get_participants(game_id)
        draw_results = await self.get_draw_results(game_id)

        return {
            "participant_count": len(participants),
            "draw_count": len(draw_results),
        }



         


