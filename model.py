###########################################################
# ORM Initialization
###########################################################
import json
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    DateTime,
    Text,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Station(Base):
    __tablename__ = 'stations'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    slug = Column(String(20), nullable=False)
    assets = relationship("Asset", back_populates="station", lazy='dynamic')

    def __repr__(self):
        return "<Station({id}/{slug}, name='{name}')>".format(id=self.id, slug=self.slug, name=self.name)

class Asset(Base):
    __tablename__ = 'assets'

    id = Column(Integer, primary_key=True)

    id_by_station = Column(Integer)
    type = Column(Enum('Song', 'Link', 'Spot', 'Unknown', 'Live'), nullable=False)
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False)
    album = Column(String(255))
    added = Column(DateTime, default=func.now())
    extra_data = Column(Text)

    station_id = Column(Integer, ForeignKey('stations.id'))
    station = relationship("Station", back_populates="assets")

    plays = relationship("Play", back_populates="asset")

    def __repr__(self):
        return "<Asset({station}, id={id}, type={type} title='{title}', artist='{artist}')>".format(
            station=self.station.slug, id=self.id_by_station, type=self.type,
            title=self.title, artist=self.artist
        )

class Play(Base):
    __tablename__ = 'plays'

    id = Column(Integer, primary_key=True)

    asset_id = Column(Integer, ForeignKey('assets.id'))
    asset = relationship("Asset", back_populates="plays")

    extra_data = Column(Text)
    timestamp = Column(DateTime, default=func.now())

    def __repr__(self):
        return "<Play({id}, {asset})>".format(id=self.id, asset=self.asset)

class Log(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True)
    priority = Column(Enum('Debug', 'Warning', 'Error'), nullable=False)
    module = Column(String(20), nullable=False)
    message = Column(String(255), nullable=False)
    extra_data = Column(Text)
    timestamp = Column(DateTime, default=func.now())

    def add_data(self, data):
        if data is None:
            return False

        if self.extra_data is not None:
            old = json.loads(self.extra_data)
        else:
            old = {}

        self.extra_data = json.dumps({**old, **data})

    def __repr__(self):
        return "<Log[{}/{}]('{}', {})>".format(self.module, self.priority, self.message, self.extra_data)
