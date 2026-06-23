from sqlalchemy.orm import Session
from app.domain.models import Player, ValorantProfile
from app.schemas.player import PlayerCreate

class PlayerRepository:
    @staticmethod
    def get_player_by_id(db: Session, player_id):
        return db.query(Player).filter(Player.id == player_id).first()

    @staticmethod
    def create_player(db: Session, player_data: PlayerCreate):
        new_player = Player(nickname=player_data.nickname, riot_id=player_data.riot_id)
        db.add(new_player)
        db.commit()
        db.refresh(new_player)
        
        new_profile = ValorantProfile(
            player_id=new_player.id,
            region=player_data.region,
            current_rank=player_data.current_rank,
            main_roles=",".join(player_data.main_roles)
        )
        db.add(new_profile)
        db.commit()
        return new_player