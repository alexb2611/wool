import enum
from sqlalchemy import Column, Float, Integer, String, Text, Enum, DateTime, func
from backend.database import Base


class YarnWeight(str, enum.Enum):
    LACE = "Lace"
    FOUR_PLY = "4 Ply"
    DK = "DK"
    ARAN = "Aran"
    WORSTED = "Worsted"
    CHUNKY = "Chunky"
    SUPER_CHUNKY = "Super Chunky"


class Yarn(Base):
    __tablename__ = "yarns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    weight = Column(Enum(YarnWeight), nullable=False)
    colour = Column(String, nullable=False)
    fibre = Column(String, nullable=False)
    metres_per_ball = Column(Integer, nullable=True)
    full_balls = Column(Integer, nullable=False, default=0)
    part_balls = Column(Integer, nullable=False, default=0)
    extra_metres = Column(Integer, nullable=True)
    estimated_total_metres = Column(Integer, nullable=True)
    intended_project = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    needle_size_mm = Column(Float, nullable=True)
    tension = Column(String, nullable=True)
    ball_weight_grams = Column(Integer, nullable=True)
    image_url = Column(String, nullable=True)
    ravelry_url = Column(String, nullable=True)
    pattern_name = Column(String, nullable=True)
    pattern_author = Column(String, nullable=True)
    pattern_suggested_yarn = Column(String, nullable=True)
    pattern_yarn_weight = Column(String, nullable=True)
    pattern_image_filename = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
