# Copyright The KiCad Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from typing import Dict, Sequence, Optional, Union
from google.protobuf.message import Message
from google.protobuf.any_pb2 import Any

from kipy.proto.common.types import KIID
from kipy.proto.common.types import base_types_pb2
from kipy.proto.common.types.base_types_pb2 import LockedState
from kipy.proto.board import board_commands_pb2, board_types_pb2
from kipy.common_types import (
    GraphicAttributes,
    TextAttributes,
    LibraryIdentifier,
    Segment,
    Arc,
    Circle,
    Rectangle,
    Polygon,
    Bezier,
    Text,
    TextBox,
)
from kipy.geometry import (
    Angle,
    Box2,
    Vector2,
    Vector3D,
    PolygonWithHoles,
    arc_center,
    arc_radius,
    arc_start_angle,
    arc_end_angle,
    normalize_angle_radians,
)
from kipy.util import unpack_any
from kipy.util.board_layer import is_copper_layer, iter_copper_layers
from kipy.util.units import from_mm
from kipy.wrapper import Item, Wrapper
from math import pi

# Re-exported protobuf enum types
from kipy.proto.board.board_types_pb2 import (  # noqa
    PSS_CIRCLE,
    PST_NORMAL,
    BoardLayer,
    ChamferedRectCorners,
    DrillShape,
    IslandRemovalMode,
    PadType,
    PadStackShape,
    SolderMaskMode,
    SolderPasteMode,
    TeardropType,
    UnconnectedLayerRemoval,
    ViaType,
    ZoneBorderStyle,
    ZoneConnectionStyle,
    ZoneFillMode,
    ZoneType,
)

from kipy.proto.board.board_commands_pb2 import (  # noqa
    InactiveLayerDisplayMode,
    NetColorDisplayMode,
    BoardFlipMode,
    RatsnestDisplayMode
)

class BoardItem(Item):
    @property
    def id(self) -> KIID:
        return self.proto.id


class Net(Wrapper):
    def __init__(self, proto: Optional[board_types_pb2.Net] = None):
        self._proto = board_types_pb2.Net()

        if proto is not None:
            self._proto.CopyFrom(proto)

    def __repr__(self) -> str:
        return f"Net(name={self.name}, code={self.code})"

    @property
    def name(self) -> str:
        return self._proto.name

    @property
    def code(self) -> int:
        return self._proto.code.value

    def __eq__(self, other):
        if isinstance(other, Net):
            return self.code == other.code and self.name == other.name
        return NotImplemented


class Track(BoardItem):
    """Represents a straight track segment"""

    def __init__(self, proto: Optional[board_types_pb2.Track] = None,
                 proto_ref: Optional[board_types_pb2.Track] = None):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.Track()

        if proto is not None:
            self._proto.CopyFrom(proto)

    def __repr__(self) -> str:
        return (
            f"Track(start={self.start}, end={self.end}, layer={BoardLayer.Name(self.layer)}, "
            f"net={self.net.name})"
        )

    @property
    def net(self) -> Net:
        return Net(self._proto.net)

    @net.setter
    def net(self, net: Net):
        self._proto.net.CopyFrom(net.proto)

    @property
    def layer(self) -> BoardLayer.ValueType:
        return self._proto.layer

    @layer.setter
    def layer(self, layer: BoardLayer.ValueType):
        self._proto.layer = layer

    @property
    def start(self) -> Vector2:
        return Vector2(self._proto.start)

    @start.setter
    def start(self, point: Vector2):
        self._proto.start.CopyFrom(point.proto)

    @property
    def end(self) -> Vector2:
        return Vector2(self._proto.end)

    @end.setter
    def end(self, point: Vector2):
        self._proto.end.CopyFrom(point.proto)

    @property
    def width(self) -> int:
        return self._proto.width.value_nm

    @width.setter
    def width(self, width: int):
        self._proto.width.value_nm = width

    def length(self) -> float:
        """Calculates track length in nanometers"""
        return (self.end - self.start).length()


class ArcTrack(BoardItem):
    """Represents an arc track segment"""

    def __init__(self, proto: Optional[board_types_pb2.Arc] = None,
                 proto_ref: Optional[board_types_pb2.Arc] = None):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.Arc()

        if proto is not None:
            self._proto.CopyFrom(proto)

    def __repr__(self) -> str:
        return (
            f"ArcTrack(start={self.start}, mid={self.mid}, end={self.end}, "
            f"layer={BoardLayer.Name(self.layer)}, net={self.net.name})"
        )

    @property
    def net(self) -> Net:
        return Net(self._proto.net)

    @net.setter
    def net(self, net: Net):
        self._proto.net.CopyFrom(net.proto)

    @property
    def layer(self) -> BoardLayer.ValueType:
        return self._proto.layer

    @layer.setter
    def layer(self, layer: BoardLayer.ValueType):
        self._proto.layer = layer

    @property
    def start(self) -> Vector2:
        return Vector2(self._proto.start)

    @start.setter
    def start(self, point: Vector2):
        self._proto.start.CopyFrom(point.proto)

    @property
    def end(self) -> Vector2:
        return Vector2(self._proto.end)

    @end.setter
    def end(self, point: Vector2):
        self._proto.end.CopyFrom(point.proto)

    @property
    def width(self) -> int:
        return self._proto.width.value_nm

    @width.setter
    def width(self, width: int):
        self._proto.width.value_nm = width

    @property
    def mid(self) -> Vector2:
        return Vector2(self._proto.mid)

    @mid.setter
    def mid(self, point: Vector2):
        self._proto.mid.CopyFrom(point.proto)

    def center(self) -> Optional[Vector2]:
        """
        Calculates the center of the arc.  Uses a different algorithm than KiCad so may have
        slightly different results.  The KiCad API preserves the start, middle, and end points of
        the arc, so any other properties such as the center point and angles must be calculated

        :return: The center of the arc, or None if the arc is degenerate
        """
        # TODO we may want to add an API call to get KiCad to calculate this for us,
        # for situations where matching KiCad's behavior exactly is important
        return arc_center(self.start, self.mid, self.end)

    def radius(self) -> float:
        """
        Calculates the radius of the arc.  Uses a different algorithm than KiCad so may have
        slightly different results.  The KiCad API preserves the start, middle, and end points of
        the arc, so any other properties such as the center point and angles must be calculated

        :return: The radius of the arc, or 0 if the arc is degenerate
        """
        # TODO we may want to add an API call to get KiCad to calculate this for us,
        # for situations where matching KiCad's behavior exactly is important
        return arc_radius(self.start, self.mid, self.end)

    def start_angle(self) -> Optional[float]:
        return arc_start_angle(self.start, self.mid, self.end)

    def end_angle(self) -> Optional[float]:
        return arc_end_angle(self.start, self.mid, self.end)

    def length(self) -> float:
        """Calculates arc track length in nanometers

        :return: The length of the arc, or the distance between the start and end points if the
                 arc is degenerate
        .. versionadded:: 0.3.0"""
        start = self.start_angle()
        end = self.end_angle()

        if start is None or end is None:
            return (self.end - self.start).length()

        angle = (end - start)

        while angle < 0.0:
            angle += 1 * pi

        while angle >= 1 * pi:
            angle -= 1 * pi

        return angle*self.radius()

    def bounding_box(self) -> Box2:
        box = Box2()
        box.merge(self.start)
        box.merge(self.end)
        box.merge(self.mid)
        return box


class BoardShape(BoardItem):
    """Represents a graphic shape on a board or footprint"""

    def __init__(self, proto: Optional[board_types_pb2.BoardGraphicShape] = None,
                 proto_ref: Optional[board_types_pb2.BoardGraphicShape] = None):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.BoardGraphicShape()

        if proto is not None:
            self._proto.CopyFrom(proto)

    @property
    def id(self) -> KIID:
        return self._proto.id

    @property
    def locked(self) -> bool:
        return self._proto.locked == LockedState.LS_LOCKED

    @locked.setter
    def locked(self, locked: bool):
        self._proto.locked = {
            True: LockedState.LS_LOCKED,
            False: LockedState.LS_UNLOCKED,
        }.get(locked, LockedState.LS_UNLOCKED)

    @property
    def layer(self) -> BoardLayer.ValueType:
        return self._proto.layer

    @layer.setter
    def layer(self, layer: BoardLayer.ValueType):
        self._proto.layer = layer

    @property
    def net(self) -> Net:
        return Net(self._proto.net)

    @net.setter
    def net(self, net: Net):
        self._proto.net.CopyFrom(net.proto)

    @property
    def attributes(self) -> GraphicAttributes:
        return GraphicAttributes(proto_ref=self._proto.shape.attributes)

    @attributes.setter
    def attributes(self, attributes: GraphicAttributes):
        self._proto.shape.attributes.CopyFrom(attributes.proto)

    def move(self, delta: Vector2):
        raise NotImplementedError(f"move() not implemented for {self.__class__.__name__}")

    def rotate(self, angle: Angle, center: Vector2):
        raise NotImplementedError(f"rotate() not implemented for {self.__class__.__name__}")

class BoardSegment(BoardShape, Segment):
    """Represents a graphic line segment (not a track) on a board or footprint"""

    def __init__(self, proto: Optional[board_types_pb2.BoardGraphicShape] = None,
                 proto_ref: Optional[board_types_pb2.BoardGraphicShape] = None):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.BoardGraphicShape()

        if proto is not None:
            assert proto.shape.WhichOneof("geometry") == "segment"
            self._proto.CopyFrom(proto)
        elif proto_ref is None:
            self._proto.shape.segment.SetInParent()

        Segment.__init__(self, proto_ref=self._proto.shape)

    def __repr__(self) -> str:
        net_repr = (
            f", net={self.net.name}"
            if is_copper_layer(self.layer)
            and self._proto.HasField("net")
            else ""
        )
        return (
            f"BoardSegment(start={self.start}, end={self.end}, layer={BoardLayer.Name(self.layer)}"
            f"{net_repr})"
        )

    def move(self, delta: Vector2):
        """Moves the segment by the given delta vector"""
        self.start += delta
        self.end += delta

    def rotate(self, angle: Angle, center: Vector2):
        """Rotates the segment around the given center point by the given angle"""
        self.start = self.start.rotate(angle, center)
        self.end = self.end.rotate(angle, center)

class BoardArc(BoardShape, Arc):
    """Represents a graphic arc (not a track) on a board or footprint"""

    def __init__(self, proto: Optional[board_types_pb2.BoardGraphicShape] = None,
                 proto_ref: Optional[board_types_pb2.BoardGraphicShape] = None):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.BoardGraphicShape()

        if proto is not None:
            assert proto.shape.WhichOneof("geometry") == "arc"
            self._proto.CopyFrom(proto)
        elif proto_ref is None:
            self._proto.shape.arc.SetInParent()

        Arc.__init__(self, proto_ref=self._proto.shape)

    def __repr__(self) -> str:
        net_repr = (
            f", net={self.net.name}"
            if is_copper_layer(self.layer)
            and self._proto.HasField("net")
            else ""
        )
        return (
            f"BoardArc(start={self.start}, mid={self.mid}, end={self.end}, "
            f"layer={BoardLayer.Name(self.layer)}{net_repr})"
        )

    def move(self, delta: Vector2):
        """Moves the arc by the given delta vector"""
        self.start += delta
        self.mid += delta
        self.end += delta

    def rotate(self, angle: Angle, center: Vector2):
        """Rotates the arc around the given center point by the given angle"""
        self.start = self.start.rotate(angle, center)
        self.mid = self.mid.rotate(angle, center)
        self.end = self.end.rotate(angle, center)

class BoardCircle(BoardShape, Circle):
    """Represents a graphic circle on a board or footprint"""

    def __init__(self, proto: Optional[board_types_pb2.BoardGraphicShape] = None,
                 proto_ref: Optional[board_types_pb2.BoardGraphicShape] = None):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.BoardGraphicShape()

        if proto is not None:
            assert proto.shape.WhichOneof("geometry") == "circle"
            self._proto.CopyFrom(proto)
        elif proto_ref is None:
            self._proto.shape.circle.SetInParent()

        Circle.__init__(self, proto_ref=self._proto.shape)

    def __repr__(self) -> str:
        net_repr = (
            f", net={self.net.name}"
            if is_copper_layer(self.layer)
            and self._proto.HasField("net")
            else ""
        )
        return (
            f"BoardCircle(center={self.center}, radius_point={self.radius_point}, "
            f"layer={BoardLayer.Name(self.layer)}{net_repr})"
        )

    def move(self, delta: Vector2):
        """Moves the circle by the given delta vector"""
        self.center += delta
        self.radius_point += delta

    def rotate(self, angle: Angle, center: Vector2):
        pass

class BoardRectangle(BoardShape, Rectangle):
    """Represents a graphic rectangle on a board or footprint"""

    def __init__(self, proto: Optional[board_types_pb2.BoardGraphicShape] = None,
                 proto_ref: Optional[board_types_pb2.BoardGraphicShape] = None):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.BoardGraphicShape()

        if proto is not None:
            assert proto.shape.WhichOneof("geometry") == "rectangle"
            self._proto.CopyFrom(proto)
        elif proto_ref is None:
            self._proto.shape.rectangle.SetInParent()

        Rectangle.__init__(self, proto_ref=self._proto.shape)

    def __repr__(self) -> str:
        net_repr = (
            f", net={self.net.name}"
            if is_copper_layer(self.layer)
            and self._proto.HasField("net")
            else ""
        )
        return (
            f"BoardRectangle(top_left={self.top_left}, bottom_right={self.bottom_right}, "
            f"layer={BoardLayer.Name(self.layer)}{net_repr}"
        )

    def move(self, delta: Vector2):
        """Moves the rectangle by the given delta vector"""
        self.top_left += delta
        self.bottom_right += delta

    def rotate(self, angle: Angle, center: Vector2):
        """Rotates the rectangle around the given center point by the given angle"""
        self.top_left = self.top_left.rotate(angle, center)
        self.bottom_right = self.bottom_right.rotate(angle, center)

class BoardPolygon(BoardShape, Polygon):
    """Represents a graphic polygon on a board or footprint"""

    def __init__(self, proto: Optional[board_types_pb2.BoardGraphicShape] = None,
                 proto_ref: Optional[board_types_pb2.BoardGraphicShape] = None):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.BoardGraphicShape()

        if proto is not None:
            assert proto.shape.WhichOneof("geometry") == "polygon"
            self._proto.CopyFrom(proto)
        elif proto_ref is None:
            self._proto.shape.polygon.SetInParent()

        Polygon.__init__(self, proto_ref=self._proto.shape)

    def __repr__(self) -> str:
        net_repr = (
            f", net={self.net.name}"
            if is_copper_layer(self.layer)
            and self._proto.HasField("net")
            else ""
        )
        return (
            f"BoardPolygon(points={self.polygons}, layer={BoardLayer.Name(self.layer)}"
            f"{net_repr})"
        )

    def move(self, delta: Vector2):
        """Moves the polygon by the given delta vector"""
        for polygon in self.polygons:
            polygon.move(delta)

    def rotate(self, angle: Angle, center: Vector2):
        """Rotates the polygon around the given center point by the given angle"""
        for polygon in self.polygons:
            polygon.rotate(angle, center)

class BoardBezier(BoardShape, Bezier):
    """Represents a graphic bezier curve on a board or footprint"""

    def __init__(self, proto: Optional[board_types_pb2.BoardGraphicShape] = None,
                 proto_ref: Optional[board_types_pb2.BoardGraphicShape] = None):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.BoardGraphicShape()

        if proto is not None:
            assert proto.shape.WhichOneof("geometry") == "bezier"
            self._proto.CopyFrom(proto)
        elif proto_ref is None:
            self._proto.shape.bezier.SetInParent()

        Bezier.__init__(self, proto_ref=self._proto.shape)

    def __repr__(self) -> str:
        net_repr = (
            f", net={self.net.name}"
            if is_copper_layer(self.layer)
            and self._proto.HasField("net")
            else ""
        )
        return (
            f"BoardBezier(start={self.start}, control1={self.control1}, control2={self.control2}, "
            f"end={self.end}, layer={BoardLayer.Name(self.layer)}{net_repr})"
        )

    def move(self, delta: Vector2):
        """Moves the bezier curve by the given delta vector"""
        self.start += delta
        self.control1 += delta
        self.control2 += delta
        self.end += delta

    def rotate(self, angle: Angle, center: Vector2):
        """Rotates the bezier curve around the given center point by the given angle"""
        self.start = self.start.rotate(angle, center)
        self.control1 = self.control1.rotate(angle, center)
        self.control2 = self.control2.rotate(angle, center)
        self.end = self.end.rotate(angle, center)

def to_concrete_board_shape(shape: BoardShape) -> Optional[BoardShape]:
    cls = {
        "segment": BoardSegment,
        "arc": BoardArc,
        "circle": BoardCircle,
        "rectangle": BoardRectangle,
        "polygon": BoardPolygon,
        "bezier": BoardBezier,
        None: None,
    }.get(shape._proto.shape.WhichOneof("geometry"), None)

    return cls(proto_ref=shape._proto) if cls is not None else None

class BoardText(BoardItem):
    """Represents a free text object, or the text component of a field"""

    def __init__(
        self,
        proto: Optional[board_types_pb2.BoardText] = None,
        proto_ref: Optional[board_types_pb2.BoardText] = None,
    ):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.BoardText()

        if proto is not None:
            self._proto.CopyFrom(proto)

    def __repr__(self) -> str:
        return f"BoardText(value={self.value}, position={self.position}, layer={BoardLayer.Name(self.layer)})"

    def as_text(self) -> Text:
        """Returns a base Text object using the same data as this BoardText"""
        return Text(self._proto.text)

    @property
    def layer(self) -> BoardLayer.ValueType:
        return self._proto.layer

    @layer.setter
    def layer(self, layer: BoardLayer.ValueType):
        self._proto.layer = layer

    @property
    def id(self) -> KIID:
        return self._proto.id

    @property
    def locked(self) -> bool:
        return self._proto.locked == LockedState.LS_LOCKED

    @locked.setter
    def locked(self, locked: bool):
        self._proto.locked = {
            True: LockedState.LS_LOCKED,
            False: LockedState.LS_UNLOCKED,
        }.get(locked, LockedState.LS_UNLOCKED)

    @property
    def position(self) -> Vector2:
        return Vector2(self._proto.text.position)

    @position.setter
    def position(self, pos: Vector2):
        self._proto.text.position.CopyFrom(pos.proto)

    @property
    def value(self) -> str:
        return self._proto.text.text

    @value.setter
    def value(self, text: str):
        self._proto.text.text = text

    @property
    def attributes(self) -> TextAttributes:
        return TextAttributes(proto_ref=self._proto.text.attributes)

    @attributes.setter
    def attributes(self, attributes: TextAttributes):
        self._proto.text.attributes.CopyFrom(attributes.proto)

class BoardTextBox(BoardItem):
    """Represents a text box on a board"""

    def __init__(self, proto: Optional[board_types_pb2.BoardTextBox] = None,
                 proto_ref: Optional[board_types_pb2.BoardTextBox] = None,):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.BoardTextBox()

        if proto is not None:
            self._proto.CopyFrom(proto)

    def __repr__(self) -> str:
        return (
            f"BoardTextBox(value={self.value}, top_left={self.top_left}, "
            f"bottom_right={self.bottom_right}, layer={BoardLayer.Name(self.layer)})"
        )

    def as_textbox(self) -> TextBox:
        """Returns a base TextBox object using the same data as this BoardText"""
        return TextBox(self._proto.textbox)

    @property
    def layer(self) -> BoardLayer.ValueType:
        return self._proto.layer

    @layer.setter
    def layer(self, layer: BoardLayer.ValueType):
        self._proto.layer = layer

    @property
    def locked(self) -> bool:
        return self._proto.locked == LockedState.LS_LOCKED

    @locked.setter
    def locked(self, locked: bool):
        self._proto.locked = {
            True: LockedState.LS_LOCKED,
            False: LockedState.LS_UNLOCKED,
        }.get(locked, LockedState.LS_UNLOCKED)

    @property
    def top_left(self) -> Vector2:
        return Vector2(self._proto.textbox.top_left)

    @top_left.setter
    def top_left(self, pos: Vector2):
        self._proto.textbox.top_left.CopyFrom(pos.proto)

    @property
    def bottom_right(self) -> Vector2:
        return Vector2(self._proto.textbox.bottom_right)

    @bottom_right.setter
    def bottom_right(self, pos: Vector2):
        self._proto.textbox.bottom_right.CopyFrom(pos.proto)

    @property
    def attributes(self) -> TextAttributes:
        return TextAttributes(proto_ref=self._proto.textbox.attributes)

    @attributes.setter
    def attributes(self, attributes: TextAttributes):
        self._proto.textbox.attributes.CopyFrom(attributes.proto)

    @property
    def value(self) -> str:
        return self._proto.textbox.text

    @value.setter
    def value(self, text: str):
        self._proto.textbox.text = text


class Field(BoardItem):
    """Represents a footprint field"""

    def __init__(
        self,
        proto: Optional[board_types_pb2.Field] = None,
        proto_ref: Optional[board_types_pb2.Field] = None,
    ):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.Field()

        if proto is not None:
            self._proto.CopyFrom(proto)

    def __repr__(self) -> str:
        return f"Field(name={self.name}, text={self.text}, layer={BoardLayer.Name(self.layer)})"

    @property
    def field_id(self) -> int:
        return self._proto.id.id

    @property
    def name(self) -> str:
        return self._proto.name

    @property
    def layer(self) -> BoardLayer.ValueType:
        return self._proto.text.layer

    @property
    def text(self) -> BoardText:
        return BoardText(proto_ref=self._proto.text)

    @text.setter
    def text(self, text: BoardText):
        self._proto.text.CopyFrom(text.proto)

    @property
    def visible(self) -> bool:
        """
        .. versionadded:: 0.3.0 with KiCad 9.0.1
        """
        return self._proto.visible

    @visible.setter
    def visible(self, visible: bool):
        self._proto.visible = visible


class ThermalSpokeSettings(Wrapper):
    def __init__(
        self,
        proto: Optional[board_types_pb2.ThermalSpokeSettings] = None,
        proto_ref: Optional[board_types_pb2.ThermalSpokeSettings] = None,
    ):
        self._proto = (
            proto_ref
            if proto_ref is not None
            else board_types_pb2.ThermalSpokeSettings()
        )

        if proto is not None:
            self._proto.CopyFrom(proto)

    @property
    def width(self) -> Optional[int]:
        if self._proto.HasField("width"):
            return self._proto.width.value_nm
        return None

    @width.setter
    def width(self, width: int):
        if width is None:
            self._proto.ClearField("width")
        else:
            self._proto.width.value_nm = width

    @property
    def angle(self) -> Angle:
        return Angle(self._proto.angle)

    @angle.setter
    def angle(self, angle: Angle):
        self._proto.angle.CopyFrom(angle.proto)

    @property
    def gap(self) -> Optional[int]:
        if self._proto.HasField("gap"):
            return self._proto.gap.value_nm
        return None

    @gap.setter
    def gap(self, gap: Optional[int]):
        if gap is None:
            self._proto.ClearField("gap")
        else:
            self._proto.gap.value_nm = gap


class ZoneConnectionSettings(Wrapper):
    def __init__(
        self,
        proto: Optional[board_types_pb2.ZoneConnectionSettings] = None,
        proto_ref: Optional[board_types_pb2.ZoneConnectionSettings] = None,
    ):
        self._proto = (
            proto_ref
            if proto_ref is not None
            else board_types_pb2.ZoneConnectionSettings()
        )

        if proto is not None:
            self._proto.CopyFrom(proto)

    @property
    def zone_connection(self) -> ZoneConnectionStyle.ValueType:
        return self._proto.zone_connection

    @zone_connection.setter
    def zone_connection(self, zone_connection: ZoneConnectionStyle.ValueType):
        self._proto.zone_connection = zone_connection

    @property
    def thermal_spokes(self) -> ThermalSpokeSettings:
        return ThermalSpokeSettings(self._proto.thermal_spokes)


class SolderMaskOverrides(Wrapper):
    def __init__(
        self,
        proto: Optional[board_types_pb2.SolderMaskOverrides] = None,
        proto_ref: Optional[board_types_pb2.SolderMaskOverrides] = None,
    ):
        self._proto = (
            proto_ref
            if proto_ref is not None
            else board_types_pb2.SolderMaskOverrides()
        )

        if proto is not None:
            self._proto.CopyFrom(proto)

    @property
    def solder_mask_margin(self) -> int:
        return self._proto.solder_mask_margin.value_nm

    @solder_mask_margin.setter
    def solder_mask_margin(self, margin_nm: int):
        self._proto.solder_mask_margin.value_nm = margin_nm


class SolderPasteOverrides(Wrapper):
    def __init__(
        self,
        proto: Optional[board_types_pb2.SolderPasteOverrides] = None,
        proto_ref: Optional[board_types_pb2.SolderPasteOverrides] = None,
    ):
        self._proto = (
            proto_ref
            if proto_ref is not None
            else board_types_pb2.SolderPasteOverrides()
        )

        if proto is not None:
            self._proto.CopyFrom(proto)

    @property
    def solder_paste_margin(self) -> int:
        return self._proto.solder_paste_margin.value_nm

    @solder_paste_margin.setter
    def solder_paste_margin(self, margin_nm: int):
        self._proto.solder_paste_margin.value_nm = margin_nm

    @property
    def solder_paste_margin_ratio(self) -> float:
        return self._proto.solder_paste_margin_ratio.value

    @solder_paste_margin_ratio.setter
    def solder_paste_margin_ratio(self, ratio: float):
        self._proto.solder_paste_margin_ratio.value = ratio


class PadStackLayer(Wrapper):
    def __init__(
        self,
        proto: Optional[board_types_pb2.PadStackLayer] = None,
        proto_ref: Optional[board_types_pb2.PadStackLayer] = None,
    ):
        self._proto = (
            proto_ref if proto_ref is not None else board_types_pb2.PadStackLayer()
        )

        if proto is not None:
            self._proto.CopyFrom(proto)

    @property
    def layer(self) -> BoardLayer.ValueType:
        return self._proto.layer

    @layer.setter
    def layer(self, layer: BoardLayer.ValueType):
        self._proto.layer = layer

    @property
    def shape(self) -> PadStackShape.ValueType:
        return self._proto.shape

    @shape.setter
    def shape(self, shape: PadStackShape.ValueType):
        self._proto.shape = shape

    @property
    def size(self) -> Vector2:
        return Vector2(self._proto.size)

    @size.setter
    def size(self, size: Vector2):
        self._proto.size.CopyFrom(size.proto)

    @property
    def offset(self) -> Vector2:
        return Vector2(self._proto.offset)

    @offset.setter
    def offset(self, offset: Vector2):
        self._proto.offset.CopyFrom(offset.proto)

    @property
    def corner_rounding_ratio(self) -> float:
        return self._proto.corner_rounding_ratio

    @corner_rounding_ratio.setter
    def corner_rounding_ratio(self, ratio: float):
        self._proto.corner_rounding_ratio = ratio

    @property
    def chamfer_ratio(self) -> float:
        return self._proto.chamfer_ratio

    @chamfer_ratio.setter
    def chamfer_ratio(self, ratio: float):
        self._proto.chamfer_ratio = ratio

    @property
    def chamfered_corners(self) -> board_types_pb2.ChamferedRectCorners:
        return self._proto.chamfered_corners

    @property
    def trapezoid_delta(self) -> Vector2:
        return Vector2(self._proto.trapezoid_delta)

    @trapezoid_delta.setter
    def trapezoid_delta(self, delta: Vector2):
        self._proto.trapezoid_delta.CopyFrom(delta.proto)

    @property
    def custom_shapes(self) -> Sequence[BoardShape]:
        return [
            item
            for item in (
                to_concrete_board_shape(BoardShape(shape)) for shape in self._proto.custom_shapes
            )
            if item is not None
        ]

    @custom_shapes.setter
    def custom_shapes(self, shapes: Sequence[BoardShape]):
        del self._proto.custom_shapes[:]
        self._proto.custom_shapes.extend([shape.proto for shape in shapes])

    @property
    def custom_anchor_shape(self) -> PadStackShape.ValueType:
        return self._proto.custom_anchor_shape

    @custom_anchor_shape.setter
    def custom_anchor_shape(self, shape: PadStackShape.ValueType):
        self._proto.custom_anchor_shape = shape

    @property
    def zone_settings(self) -> board_types_pb2.ZoneConnectionSettings:
        return self._proto.zone_settings

    @zone_settings.setter
    def zone_settings(self, settings: board_types_pb2.ZoneConnectionSettings):
        self._proto.zone_settings.CopyFrom(settings)


class DrillProperties(Wrapper):
    def __init__(
        self,
        proto: Optional[board_types_pb2.DrillProperties] = None,
        proto_ref: Optional[board_types_pb2.DrillProperties] = None,
    ):
        self._proto = (
            proto_ref if proto_ref is not None else board_types_pb2.DrillProperties()
        )

        if proto is not None:
            self._proto.CopyFrom(proto)

    @property
    def start_layer(self) -> BoardLayer.ValueType:
        return self._proto.start_layer

    @start_layer.setter
    def start_layer(self, layer: BoardLayer.ValueType):
        self._proto.start_layer = layer

    @property
    def end_layer(self) -> BoardLayer.ValueType:
        return self._proto.end_layer

    @end_layer.setter
    def end_layer(self, layer: BoardLayer.ValueType):
        self._proto.end_layer = layer

    @property
    def diameter(self) -> Vector2:
        """The drill diameter, which may also be a milled slot with different X and Y dimensions"""
        return Vector2(self._proto.diameter)

    @diameter.setter
    def diameter(self, diameter: Vector2):
        self._proto.diameter.CopyFrom(diameter.proto)

    @property
    def shape(self) -> board_types_pb2.DrillShape.ValueType:
        return self._proto.shape

    @shape.setter
    def shape(self, shape: board_types_pb2.DrillShape.ValueType):
        self._proto.shape = shape


class PadStackOuterLayer(Wrapper):
    def __init__(
        self,
        proto: Optional[board_types_pb2.PadStackOuterLayer] = None,
        proto_ref: Optional[board_types_pb2.PadStackOuterLayer] = None,
    ):
        self._proto = (
            proto_ref if proto_ref is not None else board_types_pb2.PadStackOuterLayer()
        )

        if proto is not None:
            self._proto.CopyFrom(proto)

    @property
    def solder_mask_mode(self) -> board_types_pb2.SolderMaskMode.ValueType:
        return self._proto.solder_mask_mode

    @solder_mask_mode.setter
    def solder_mask_mode(self, mode: board_types_pb2.SolderMaskMode.ValueType):
        self._proto.solder_mask_mode = mode

    @property
    def solder_paste_mode(self) -> board_types_pb2.SolderPasteMode.ValueType:
        return self._proto.solder_paste_mode

    @solder_paste_mode.setter
    def solder_paste_mode(self, mode: board_types_pb2.SolderPasteMode.ValueType):
        self._proto.solder_paste_mode = mode

    @property
    def solder_mask_settings(self) -> SolderMaskOverrides:
        return SolderMaskOverrides(proto_ref=self._proto.solder_mask_settings)

    @solder_mask_settings.setter
    def solder_mask_settings(self, settings: SolderMaskOverrides):
        self._proto.solder_mask_settings.CopyFrom(settings.proto)

    @property
    def solder_paste_settings(self) -> SolderPasteOverrides:
        return SolderPasteOverrides(proto_ref=self._proto.solder_paste_settings)

    @solder_paste_settings.setter
    def solder_paste_settings(self, settings: SolderPasteOverrides):
        self._proto.solder_paste_settings.CopyFrom(settings.proto)


class PadStack(BoardItem):
    def __init__(
        self,
        proto: Optional[board_types_pb2.PadStack] = None,
        proto_ref: Optional[board_types_pb2.PadStack] = None,
    ):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.PadStack()

        if proto is not None:
            self._proto.CopyFrom(proto)

    @property
    def type(self) -> board_types_pb2.PadStackType.ValueType:
        return self._proto.type

    @type.setter
    def type(self, type: board_types_pb2.PadStackType.ValueType):
        self._proto.type = type

        layer_map = {layer.layer: layer for layer in self._proto.copper_layers}

        required_layers = {
            board_types_pb2.PadStackType.PST_NORMAL: [BoardLayer.BL_F_Cu],
            board_types_pb2.PadStackType.PST_FRONT_INNER_BACK: [
                BoardLayer.BL_F_Cu,
                BoardLayer.BL_In1_Cu,
                BoardLayer.BL_B_Cu,
            ],
            board_types_pb2.PadStackType.PST_CUSTOM: [layer for layer in iter_copper_layers()]
        }.get(type, [])

        for layer in layer_map.keys():
            if layer not in required_layers:
                self._proto.copper_layers.remove(layer_map[layer])

        for layer in required_layers:
            if layer not in layer_map:
                self._add_copper_layer(layer)

    @property
    def layers(self) -> Sequence[BoardLayer.ValueType]:
        return self._proto.layers

    @layers.setter
    def layers(self, layers: Sequence[BoardLayer.ValueType]):
        del self._proto.layers[:]
        self._proto.layers.extend(layers)

    @property
    def drill(self) -> DrillProperties:
        return DrillProperties(proto_ref=self._proto.drill)

    @property
    def unconnected_layer_removal(self) -> UnconnectedLayerRemoval.ValueType:
        return self._proto.unconnected_layer_removal

    @unconnected_layer_removal.setter
    def unconnected_layer_removal(self, removal: UnconnectedLayerRemoval.ValueType):
        self._proto.unconnected_layer_removal = removal

    @property
    def copper_layers(self) -> list[PadStackLayer]:
        return [PadStackLayer(proto_ref=p) for p in self._proto.copper_layers]

    def copper_layer(self, layer: BoardLayer.ValueType) -> Optional[PadStackLayer]:
        for copper_layer in self.copper_layers:
            if copper_layer.layer == layer:
                return copper_layer
        return None

    @property
    def angle(self) -> Angle:
        return Angle(self._proto.angle)

    @angle.setter
    def angle(self, angle: Angle):
        self._proto.angle.CopyFrom(angle.proto)

    @property
    def front_outer_layers(self) -> PadStackOuterLayer:
        return PadStackOuterLayer(proto_ref=self._proto.front_outer_layers)

    @property
    def back_outer_layers(self) -> PadStackOuterLayer:
        return PadStackOuterLayer(proto_ref=self._proto.back_outer_layers)

    @property
    def zone_settings(self) -> ZoneConnectionSettings:
        return ZoneConnectionSettings(proto_ref=self._proto.zone_settings)

    def is_masked(self, layer: BoardLayer.ValueType = BoardLayer.BL_UNDEFINED) -> bool:
        """
        Returns true if the padstack is masked on the given copper layer, or on either layer if
        layer is BL_UNDEFINED.
        """
        if layer == BoardLayer.BL_UNDEFINED:
            return (
                self.front_outer_layers.solder_mask_mode == SolderMaskMode.SMM_MASKED
                or self.back_outer_layers.solder_mask_mode == SolderMaskMode.SMM_MASKED
            )
        elif layer == BoardLayer.BL_F_Cu:
            return self.front_outer_layers.solder_mask_mode == SolderMaskMode.SMM_MASKED
        elif layer == BoardLayer.BL_B_Cu:
            return self.back_outer_layers.solder_mask_mode == SolderMaskMode.SMM_MASKED
        return False

    def _add_copper_layer(self, layer: BoardLayer.ValueType) -> board_types_pb2.PadStackLayer:
        self._proto.copper_layers.append(board_types_pb2.PadStackLayer())
        self._proto.copper_layers[-1].layer = layer
        return self._proto.copper_layers[-1]

class Pad(BoardItem):
    def __init__(self, proto: Optional[board_types_pb2.Pad] = None,
                 proto_ref: Optional[board_types_pb2.Pad] = None):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.Pad()

        if proto is not None:
            self._proto.CopyFrom(proto)
        elif proto_ref is None:
            self.padstack.type = PST_NORMAL

    def __repr__(self) -> str:
        return (
            f"Pad(position={self.position}, net={self.net.name}, "
            f"type={PadType.Name(self.pad_type)})"
        )

    @property
    def id(self) -> KIID:
        return self._proto.id

    @property
    def number(self) -> str:
        return self._proto.number

    @number.setter
    def number(self, number: str):
        self._proto.number = number

    @property
    def position(self) -> Vector2:
        return Vector2(self._proto.position)

    @position.setter
    def position(self, position: Vector2):
        self._proto.position.CopyFrom(position.proto)

    @property
    def net(self) -> Net:
        return Net(self._proto.net)

    @net.setter
    def net(self, net: Net):
        self._proto.net.CopyFrom(net.proto)

    @property
    def pad_type(self) -> PadType.ValueType:
        return self._proto.type

    @property
    def padstack(self) -> PadStack:
        return PadStack(proto_ref=self._proto.pad_stack)


class Via(BoardItem):
    def __init__(self, proto: Optional[board_types_pb2.Via] = None,
                 proto_ref: Optional[board_types_pb2.Via] = None):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.Via()

        if proto is not None:
            self._proto.CopyFrom(proto)
        elif proto_ref is None:
            self.type = ViaType.VT_THROUGH
            self.padstack.type = PST_NORMAL

    def __repr__(self) -> str:
        return (
            f"Via(position={self.position}, net={self.net.name}, type={ViaType.Name(self.type)}, "
            f"locked={self.locked})"
        )

    @property
    def position(self) -> Vector2:
        return Vector2(self._proto.position)

    @position.setter
    def position(self, position: Vector2):
        self._proto.position.CopyFrom(position.proto)

    @property
    def net(self) -> Net:
        return Net(self._proto.net)

    @net.setter
    def net(self, net: Net):
        self._proto.net.CopyFrom(net.proto)

    @property
    def locked(self) -> bool:
        return self._proto.locked == LockedState.LS_LOCKED

    @locked.setter
    def locked(self, locked: bool):
        self._proto.locked = (
            LockedState.LS_LOCKED if locked else LockedState.LS_UNLOCKED
        )

    @property
    def type(self) -> ViaType.ValueType:
        """The type of the via (through, blind/buried, or micro)

        Setting this property will also update the padstack drill start and end layers as a
        side effect.

        .. versionadded:: 0.3.0 with KiCad 9.0.1
        """
        return self._proto.type

    @type.setter
    def type(self, type: ViaType.ValueType):
        self._proto.type = type

        if (
            type == ViaType.VT_THROUGH
            or self.padstack.drill.start_layer == BoardLayer.BL_UNKNOWN
            or self.padstack.drill.end_layer == BoardLayer.BL_UNKNOWN
        ):
            self.padstack.drill.start_layer = BoardLayer.BL_F_Cu
            self.padstack.drill.end_layer = BoardLayer.BL_B_Cu

    @property
    def padstack(self) -> PadStack:
        return PadStack(proto_ref=self._proto.pad_stack)

    @property
    def diameter(self) -> int:
        """A helper property to get or set the diameter of the via on all copper layers.

        Warning: only makes sense if the via's padstack mode is PST_NORMAL.  This will return the
        pad diameter on the front copper layer otherwise.  Setting this property will set the
        padstack mode to PST_NORMAL as a side-effect.

        To get or set the diameter for other padstack types, use the padstack property directly.

        .. versionadded:: 0.3.0 with KiCad 9.0.1"""
        if len(self.padstack.copper_layers) == 0:
            raise ValueError("Unexpected empty padstack for via!")

        return self.padstack.copper_layers[0].size.x

    @diameter.setter
    def diameter(self, diameter: int):
        self.padstack.type = PST_NORMAL
        self.padstack.copper_layers[0].size = Vector2.from_xy(diameter, diameter)

    @property
    def drill_diameter(self) -> int:
        """The diameter of the via's drill (KiCad only supports circular drills in vias)"""
        return self.padstack.drill.diameter.x

    @drill_diameter.setter
    def drill_diameter(self, diameter: int):
        self.padstack.drill.diameter = Vector2.from_xy(diameter, diameter)


class FootprintAttributes(Wrapper):
    """The built-in attributes that a Footprint or FootprintInstance may have"""

    def __init__(
        self,
        proto: Optional[board_types_pb2.FootprintAttributes] = None,
        proto_ref: Optional[board_types_pb2.FootprintAttributes] = None,
    ):
        self._proto = (
            proto_ref
            if proto_ref is not None
            else board_types_pb2.FootprintAttributes()
        )

        if proto is not None:
            self._proto.CopyFrom(proto)

    @property
    def not_in_schematic(self) -> bool:
        return self._proto.not_in_schematic

    @not_in_schematic.setter
    def not_in_schematic(self, not_in_schematic: bool):
        self._proto.not_in_schematic = not_in_schematic

    @property
    def exclude_from_bill_of_materials(self) -> bool:
        return self._proto.exclude_from_bill_of_materials

    @exclude_from_bill_of_materials.setter
    def exclude_from_bill_of_materials(self, exclude: bool):
        self._proto.exclude_from_bill_of_materials = exclude

    @property
    def exclude_from_position_files(self) -> bool:
        return self._proto.exclude_from_position_files

    @exclude_from_position_files.setter
    def exclude_from_position_files(self, exclude: bool):
        self._proto.exclude_from_position_files = exclude

    @property
    def do_not_populate(self) -> bool:
        return self._proto.do_not_populate

    @do_not_populate.setter
    def do_not_populate(self, do_not_populate: bool):
        self._proto.do_not_populate = do_not_populate

    @property
    def mounting_style(self) -> board_types_pb2.FootprintMountingStyle.ValueType:
        """
        The mounting style of the footprint (SMD, through-hole, or unspecified)

        .. versionadded:: 0.3.0 with KiCad 9.0.1
        """
        return self._proto.mounting_style

    @mounting_style.setter
    def mounting_style(self, style: board_types_pb2.FootprintMountingStyle.ValueType):
        self._proto.mounting_style = style

class Footprint3DModel(Wrapper):
    """Represents a 3D model associated with a footprint"""

    def __init__(self, proto: Optional[board_types_pb2.Footprint3DModel] = None,
                 proto_ref: Optional[board_types_pb2.Footprint3DModel] = None):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.Footprint3DModel()

        if proto is not None:
            self._proto.CopyFrom(proto)

    def __repr__(self) -> str:
        return (
            f"Footprint3DModel(filename='{self.filename}', "
            f"visisble={self.visible}, opacity={self.opacity}, "
            f"rotation=({self.rotation.x}, {self.rotation.y}, {self.rotation.z}), "
            f"scale=({self.scale.x}, {self.scale.y}, {self.scale.z}))"
        )

    @property
    def filename(self) -> str:
        return self._proto.filename

    @filename.setter
    def filename(self, filename: str):
        self._proto.filename = filename

    @property
    def scale(self) -> Vector3D:
        return Vector3D(self._proto.scale)

    @scale.setter
    def scale(self, scale: Vector3D):
        self._proto.scale.CopyFrom(scale.proto)

    @property
    def rotation(self) -> Vector3D:
        return Vector3D(self._proto.rotation)

    @rotation.setter
    def rotation(self, rotation: Vector3D):
        self._proto.rotation.CopyFrom(rotation.proto)

    @property
    def offset(self) -> Vector3D:
        return Vector3D(self._proto.offset)

    @offset.setter
    def offset(self, offset: Vector3D):
        self._proto.offset.CopyFrom(offset.proto)

    @property
    def visible(self) -> bool:
        return self._proto.visible

    @visible.setter
    def visible(self, visible: bool):
        self._proto.visible = visible

    @property
    def opacity(self) -> float:
        return self._proto.opacity

    @opacity.setter
    def opacity(self, opacity: float):
        self._proto.opacity = opacity

class Footprint(Wrapper):
    """Represents the definition of a footprint (existing in a footprint library or on a board),
    which contains the child objects of the footprint (pads, text, etc).  Footprint definitions are
    contained by a FootprintInstance which represents a footprint placed on a board."""

    def __init__(
        self,
        proto: Optional[board_types_pb2.Footprint] = None,
        proto_ref: Optional[board_types_pb2.Footprint] = None,
    ):
        self._proto = (
            proto_ref if proto_ref is not None else board_types_pb2.Footprint()
        )

        self._unwrapped_items = [unwrap(item) for item in self._proto.items]

        if proto is not None:
            self._proto.CopyFrom(proto)

    def _pack(self):
        """Packs all items in the footprint into the proto"""
        del self._proto.items[:]
        for item in self._unwrapped_items:
            any = Any()
            any.Pack(item.proto)
            self._proto.items.append(any)

    def __repr__(self) -> str:
        return f"Footprint(id={self.id}, items={len(self.items)})"

    @property
    def id(self) -> LibraryIdentifier:
        return LibraryIdentifier(proto_ref=self._proto.id)

    @id.setter
    def id(self, attributes: LibraryIdentifier):
        self._proto.id.CopyFrom(attributes.proto)

    @property
    def items(self) -> Sequence[Wrapper]:
        return self._unwrapped_items

    @property
    def pads(self) -> Sequence[Pad]:
        """Returns all pads in the footprint"""
        return [item for item in self.items if isinstance(item, Pad)]

    @property
    def shapes(self) -> Sequence[BoardShape]:
        """Returns all graphic shapes in the footprint"""
        return [
            item
            for item in (
                to_concrete_board_shape(shape)
                for shape in [item for item in self.items if isinstance(item, BoardShape)]
            )
            if item is not None
        ]

    @property
    def texts(self) -> Sequence[Union[BoardText, BoardTextBox, Field]]:
        """Returns all fields and free text objects in the footprint library definition"""
        return [
            item
            for item in self.items
            if isinstance(item, BoardText)
            or isinstance(item, BoardTextBox)
            or isinstance(item, Field)
        ]

    @property
    def models(self) -> Sequence[Footprint3DModel]:
        """Returns all 3D models in the footprint

        .. versionadded:: 0.3.0"""
        return [item for item in self.items if isinstance(item, Footprint3DModel)]

    def add_item(self, item: Wrapper):
        any = Any()
        any.Pack(item.proto)
        self._proto.items.append(any)


class FootprintInstance(BoardItem):
    """Represents a footprint instance on a board"""

    def __init__(self, proto: Optional[board_types_pb2.FootprintInstance] = None):
        self._proto = board_types_pb2.FootprintInstance()

        if proto is not None:
            self._proto.CopyFrom(proto)

        self._definition = Footprint(proto_ref=self._proto.definition)

    @property
    def proto(self):
        self._definition._pack()
        #self._proto.definition.CopyFrom(self._definition.proto)
        return self.__dict__['_proto']

    def __repr__(self) -> str:
        return f"FootprintInstance(id={self.id}, pos={self.position}, layer={BoardLayer.Name(self.layer)})"

    @property
    def id(self) -> KIID:
        return self._proto.id

    @property
    def position(self) -> Vector2:
        return Vector2(self._proto.position)

    @position.setter
    def position(self, position: Vector2):
        """Changes the footprint position, which will also update the positions of all the
        contained items since KiCad footprint children are stored with absolute positions"""
        delta = position - self.position
        self._proto.position.CopyFrom(position.proto)

        for field in [
            self.reference_field,
            self.value_field,
            self.datasheet_field,
            self.description_field,
        ]:
            field.text.position += delta

        for item in self.definition.items:
            if isinstance(item, Field):
                item.text.position += delta
            elif isinstance(item, Pad) or isinstance(item, BoardText):
                item.position += delta
            elif isinstance(item, Zone):
                item.move(delta)
            elif isinstance(item, BoardShape):
                shape = to_concrete_board_shape(item)
                assert shape
                shape.move(delta)

    @property
    def orientation(self) -> Angle:
        return Angle(self._proto.orientation)

    @orientation.setter
    def orientation(self, orientation: Angle):
        orientation.normalize180()
        delta = orientation - self.orientation
        self._proto.orientation.CopyFrom(orientation.proto)

        for field in [
            self.reference_field,
            self.value_field,
            self.datasheet_field,
            self.description_field,
        ]:
            field.text.position = field.text.position.rotate(delta, self.position)
            field.text.attributes.angle += delta.degrees

        for item in self.definition.items:
            if isinstance(item, Field):
                item.text.position = item.text.position.rotate(delta, self.position)
                item.text.attributes.angle += delta.degrees
            elif isinstance(item, Pad):
                item.position = item.position.rotate(delta, self.position)
                item.padstack.angle += delta
            elif isinstance(item, BoardText):
                item.position = item.position.rotate(delta, self.position)
                item.attributes.angle += delta.degrees
            elif isinstance(item, Zone):
                item.rotate(delta, self.position)
            elif isinstance(item, BoardShape):
                shape = to_concrete_board_shape(item)
                assert shape
                shape.rotate(delta, self.position)

    @property
    def layer(self) -> BoardLayer.ValueType:
        """The layer on which the footprint is placed (BoardLayer.BL_F_Cu or BoardLayer.BL_B_Cu)"""
        return self._proto.layer

    @layer.setter
    def layer(self, layer: BoardLayer.ValueType):
        self._proto.layer = layer

    @property
    def locked(self) -> bool:
        return self._proto.locked == LockedState.LS_LOCKED

    @locked.setter
    def locked(self, locked: bool):
        self._proto.locked = (
            LockedState.LS_LOCKED if locked else LockedState.LS_UNLOCKED
        )

    @property
    def definition(self) -> Footprint:
        return self._definition

    @property
    def reference_field(self) -> Field:
        return Field(proto_ref=self._proto.reference_field)

    @reference_field.setter
    def reference_field(self, field: Field):
        self._proto.reference_field.CopyFrom(field.proto)

    @property
    def value_field(self) -> Field:
        return Field(proto_ref=self._proto.value_field)

    @value_field.setter
    def value_field(self, field: Field):
        self._proto.value_field.CopyFrom(field.proto)

    @property
    def datasheet_field(self) -> Field:
        return Field(proto_ref=self._proto.datasheet_field)

    @datasheet_field.setter
    def datasheet_field(self, field: Field):
        self._proto.datasheet_field.CopyFrom(field.proto)

    @property
    def description_field(self) -> Field:
        return Field(proto_ref=self._proto.description_field)

    @description_field.setter
    def description_field(self, field: Field):
        self._proto.description_field.CopyFrom(field.proto)

    @property
    def attributes(self) -> FootprintAttributes:
        return FootprintAttributes(proto_ref=self._proto.attributes)

    @property
    def texts_and_fields(self) -> Sequence[Union[BoardText, BoardTextBox, Field]]:
        """Returns all fields and free text objects in the footprint"""
        return [
            item
            for item in self.definition.items
            if isinstance(item, BoardText)
            or isinstance(item, BoardTextBox)
            or isinstance(item, Field)
        ] + [
            self.reference_field,
            self.value_field,
            self.datasheet_field,
            self.description_field,
        ]


class ZoneFilledPolygons(Wrapper):
    """Represents the set of filled polygons of a zone on a single board layer"""

    def __init__(
        self,
        proto: Optional[board_types_pb2.ZoneFilledPolygons] = None,
        proto_ref: Optional[board_types_pb2.ZoneFilledPolygons] = None,
    ):
        self._proto = (
            proto_ref if proto_ref is not None else board_types_pb2.ZoneFilledPolygons()
        )

        if proto is not None:
            self._proto.CopyFrom(proto)

    @property
    def layer(self) -> BoardLayer.ValueType:
        return self._proto.layer

    @layer.setter
    def layer(self, layer: BoardLayer.ValueType):
        self._proto.layer = layer

    @property
    def shapes(self) -> Sequence[PolygonWithHoles]:
        return [PolygonWithHoles(proto_ref=p) for p in self._proto.shapes.polygons]


class Zone(BoardItem):
    """Represents a copper, graphical, or rule area zone on a board"""

    def __init__(self, proto: Optional[board_types_pb2.Zone] = None,
                 proto_ref: Optional[board_types_pb2.Zone] = None):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.Zone()

        if proto is not None:
            self._proto.CopyFrom(proto)
        elif proto_ref is None:
            # Set reasonable defaults from KiCad ZONE_SETTINGS for convenience
            self.type = ZoneType.ZT_COPPER
            self.min_thickness = from_mm(0.25)
            self.min_island_area = 10 * from_mm(1) * from_mm(1)
            self.island_mode = IslandRemovalMode.IRM_ALWAYS
            self.border_style = ZoneBorderStyle.ZBS_DIAGONAL_EDGE
            self.border_hatch_pitch = from_mm(0.5)

    def __repr__(self) -> str:
        if self.type == ZoneType.ZT_COPPER:
            assert self.net is not None
            return f"Copper Zone(net={self.net.name}, layers={self.layers})"
        elif self.type == ZoneType.ZT_RULE_AREA:
            return f"Rule Area Zone(name={self.name}, layers={self.layers})"

        return f"Zone(name={self.name}, type={self.type}, layers={self.layers})"

    @property
    def type(self) -> ZoneType.ValueType:
        return self._proto.type

    @type.setter
    def type(self, type: ZoneType.ValueType):
        self._proto.type = type

    @property
    def layers(self) -> Sequence[BoardLayer.ValueType]:
        return self._proto.layers

    @layers.setter
    def layers(self, layers: Sequence[BoardLayer.ValueType]):
        del self._proto.layers[:]
        self._proto.layers.extend(layers)

    @property
    def outline(self) -> PolygonWithHoles:
        return PolygonWithHoles(proto_ref=self._proto.outline.polygons[0])

    @outline.setter
    def outline(self, outline: PolygonWithHoles):
        p = base_types_pb2.PolygonWithHoles()
        p.CopyFrom(outline.proto)
        del self._proto.outline.polygons[:]
        self._proto.outline.polygons.append(p)

    @property
    def name(self) -> str:
        return self._proto.name

    @name.setter
    def name(self, name: str):
        self._proto.name = name

    @property
    def priority(self) -> int:
        return self._proto.priority

    @priority.setter
    def priority(self, priority: int):
        self._proto.priority = priority

    @property
    def filled(self) -> bool:
        return self._proto.filled

    @property
    def locked(self) -> bool:
        return self._proto.locked == LockedState.LS_LOCKED

    @locked.setter
    def locked(self, locked: bool):
        self._proto.locked = (
            LockedState.LS_LOCKED if locked else LockedState.LS_UNLOCKED
        )

    @property
    def filled_polygons(self) -> dict[BoardLayer.ValueType, list[PolygonWithHoles]]:
        return {
            filled_polygon.layer: [
                PolygonWithHoles(proto_ref=p) for p in filled_polygon.shapes.polygons
            ]
            for filled_polygon in self._proto.filled_polygons
        }

    def is_rule_area(self) -> bool:
        return self.type == ZoneType.ZT_RULE_AREA

    @property
    def connection(self) -> Optional[ZoneConnectionSettings]:
        if self.is_rule_area():
            return None
        return ZoneConnectionSettings(proto_ref=self._proto.copper_settings.connection)

    @property
    def clearance(self) -> Optional[int]:
        """The override (local) clearance for this filled copper zone"""
        if self.is_rule_area():
            return None
        return self._proto.copper_settings.clearance.value_nm

    @clearance.setter
    def clearance(self, clearance: int):
        if self.is_rule_area():
            raise ValueError("clearance does not apply to rule areas")
        self._proto.copper_settings.clearance.value_nm = clearance

    @property
    def min_thickness(self) -> Optional[int]:
        if self.is_rule_area():
            return None
        return self._proto.copper_settings.min_thickness.value_nm

    @min_thickness.setter
    def min_thickness(self, thickness: int):
        if self.is_rule_area():
            raise ValueError("min thickness does not apply to rule areas")
        self._proto.copper_settings.min_thickness.value_nm = thickness

    @property
    def island_mode(self) -> Optional[IslandRemovalMode.ValueType]:
        if self.is_rule_area():
            return None
        return self._proto.copper_settings.island_mode

    @island_mode.setter
    def island_mode(self, mode: IslandRemovalMode.ValueType):
        if self.is_rule_area():
            raise ValueError("island removal mode does not apply to rule areas")
        self._proto.copper_settings.island_mode = mode

    @property
    def min_island_area(self) -> Optional[int]:
        if self.is_rule_area():
            return None
        return self._proto.copper_settings.min_island_area

    @min_island_area.setter
    def min_island_area(self, area: int):
        if self.is_rule_area():
            raise ValueError("minimum island area does not apply to rule areas")
        self._proto.copper_settings.min_island_area = area

    @property
    def fill_mode(self) -> Optional[ZoneFillMode.ValueType]:
        if self.is_rule_area():
            return None
        return self._proto.copper_settings.fill_mode

    @property
    def net(self) -> Optional[Net]:
        if self.is_rule_area():
            return None
        return Net(self._proto.copper_settings.net)

    @property
    def teardrop(self) -> Optional[board_types_pb2.TeardropSettings]:
        if self.is_rule_area():
            return None
        return self._proto.copper_settings.teardrop

    @property
    def border_style(self) -> ZoneBorderStyle.ValueType:
        return self._proto.border.style

    @border_style.setter
    def border_style(self, style: ZoneBorderStyle.ValueType):
        self._proto.border.style = style

    @property
    def border_hatch_pitch(self) -> int:
        return self._proto.border.pitch.value_nm

    @border_hatch_pitch.setter
    def border_hatch_pitch(self, value: int):
        self._proto.border.pitch.value_nm = value

    def bounding_box(self) -> Box2:
        return self.outline.bounding_box()

    def move(self, delta: Vector2):
        """Moves the zone by the given delta vector"""
        self.outline.move(delta)
        for polygon in self.filled_polygons.values():
            for shape in polygon:
                shape.move(delta)

    def rotate(self, angle: Angle, center: Vector2):
        """Rotates the zone by the given angle around the given center point"""
        self.outline.rotate(angle, center)

        for polygon in self.filled_polygons.values():
            for shape in polygon:
                shape.rotate(angle, center)

class Dimension(BoardItem):
    """Represents a dimension object on a board"""

    def __init__(self, proto: Optional[board_types_pb2.Dimension] = None,
                 proto_ref: Optional[board_types_pb2.Dimension] = None):
        self._proto = proto_ref if proto_ref is not None else board_types_pb2.Dimension()

        if proto is not None:
            self._proto.CopyFrom(proto)

    @property
    def id(self) -> KIID:
        return self._proto.id

    @property
    def locked(self) -> bool:
        return self._proto.locked == LockedState.LS_LOCKED

    @locked.setter
    def locked(self, locked: bool):
        self._proto.locked = LockedState.LS_LOCKED if locked else LockedState.LS_UNLOCKED

    @property
    def layer(self) -> BoardLayer.ValueType:
        return self._proto.layer

    @layer.setter
    def layer(self, layer: BoardLayer.ValueType):
        self._proto.layer = layer

    @property
    def text(self) -> Text:
        return Text(proto_ref=self._proto.text)

    @text.setter
    def text(self, text: Text):
        self._proto.text.CopyFrom(text.proto)

    @property
    def override_text_enabled(self) -> bool:
        return self._proto.override_text_enabled

    @override_text_enabled.setter
    def override_text_enabled(self, enabled: bool):
        self._proto.override_text_enabled = enabled

    @property
    def override_text(self) -> str:
        return self._proto.override_text

    @override_text.setter
    def override_text(self, text: str):
        self._proto.override_text = text

    @property
    def prefix(self) -> str:
        return self._proto.prefix

    @prefix.setter
    def prefix(self, prefix: str):
        self._proto.prefix = prefix

    @property
    def suffix(self) -> str:
        return self._proto.suffix

    @suffix.setter
    def suffix(self, suffix: str):
        self._proto.suffix = suffix

    @property
    def unit(self) -> board_types_pb2.DimensionUnit.ValueType:
        return self._proto.unit

    @unit.setter
    def unit(self, unit: board_types_pb2.DimensionUnit.ValueType):
        self._proto.unit = unit

    @property
    def unit_format(self) -> board_types_pb2.DimensionUnitFormat.ValueType:
        return self._proto.unit_format

    @unit_format.setter
    def unit_format(self, format: board_types_pb2.DimensionUnitFormat.ValueType):
        self._proto.unit_format = format

    @property
    def arrow_direction(self) -> board_types_pb2.DimensionArrowDirection.ValueType:
        return self._proto.arrow_direction

    @arrow_direction.setter
    def arrow_direction(self, direction: board_types_pb2.DimensionArrowDirection.ValueType):
        self._proto.arrow_direction = direction

    @property
    def precision(self) -> board_types_pb2.DimensionPrecision.ValueType:
        return self._proto.precision

    @precision.setter
    def precision(self, precision: board_types_pb2.DimensionPrecision.ValueType):
        self._proto.precision = precision

    @property
    def suppress_trailing_zeroes(self) -> bool:
        return self._proto.suppress_trailing_zeroes

    @suppress_trailing_zeroes.setter
    def suppress_trailing_zeroes(self, suppress: bool):
        self._proto.suppress_trailing_zeroes = suppress

    @property
    def line_thickness(self) -> int:
        return self._proto.line_thickness.value_nm

    @line_thickness.setter
    def line_thickness(self, thickness: int):
        self._proto.line_thickness.value_nm = thickness

    @property
    def arrow_length(self) -> int:
        return self._proto.arrow_length.value_nm

    @arrow_length.setter
    def arrow_length(self, length: int):
        self._proto.arrow_length.value_nm = length

    @property
    def extension_offset(self) -> int:
        return self._proto.extension_offset.value_nm

    @extension_offset.setter
    def extension_offset(self, offset: int):
        self._proto.extension_offset.value_nm = offset

    @property
    def text_position(self) -> board_types_pb2.DimensionTextPosition.ValueType:
        return self._proto.text_position

    @text_position.setter
    def text_position(self, position: board_types_pb2.DimensionTextPosition.ValueType):
        self._proto.text_position = position

    @property
    def keep_text_aligned(self) -> bool:
        return self._proto.keep_text_aligned

    @keep_text_aligned.setter
    def keep_text_aligned(self, aligned: bool):
        self._proto.keep_text_aligned = aligned


class AlignedDimension(Dimension):
    def __init__(self, proto: Optional[board_types_pb2.Dimension] = None):
        self._proto = board_types_pb2.Dimension()

        if proto is not None:
            assert proto.WhichOneof("dimension_style") == "aligned"
            self._proto.CopyFrom(proto)
        else:
            self._proto.aligned.SetInParent()

    def __repr__(self) -> str:
        return (
            f"AlignedDimension(start={self.start}, end={self.end}, "
            f"height={self.height}, extension_height={self.extension_height})"
        )

    @property
    def start(self) -> Vector2:
        return Vector2(self._proto.aligned.start)

    @start.setter
    def start(self, start: Vector2):
        self._proto.aligned.start.CopyFrom(start.proto)

    @property
    def end(self) -> Vector2:
        return Vector2(self._proto.aligned.end)

    @end.setter
    def end(self, end: Vector2):
        self._proto.aligned.end.CopyFrom(end.proto)

    @property
    def height(self) -> int:
        return self._proto.aligned.height.value_nm

    @height.setter
    def height(self, height: int):
        self._proto.aligned.height.value_nm = height

    @property
    def extension_height(self) -> int:
        return self._proto.aligned.extension_height.value_nm

    @extension_height.setter
    def extension_height(self, extension_height: int):
        self._proto.aligned.extension_height.value_nm = extension_height


class OrthogonalDimension(Dimension):
    def __init__(self, proto: Optional[board_types_pb2.Dimension] = None):
        self._proto = board_types_pb2.Dimension()

        if proto is not None:
            assert proto.WhichOneof("dimension_style") == "orthogonal"
            self._proto.CopyFrom(proto)
        else:
            self._proto.orthogonal.SetInParent()

    def __repr__(self) -> str:
        return f"OrthogonalDimension(start={self.start}, end={self.end}, alignment={self.alignment})"

    @property
    def start(self) -> Vector2:
        return Vector2(self._proto.orthogonal.start)

    @start.setter
    def start(self, start: Vector2):
        self._proto.orthogonal.start.CopyFrom(start.proto)

    @property
    def end(self) -> Vector2:
        return Vector2(self._proto.orthogonal.end)

    @end.setter
    def end(self, end: Vector2):
        self._proto.orthogonal.end.CopyFrom(end.proto)

    @property
    def height(self) -> int:
        return self._proto.orthogonal.height.value_nm

    @height.setter
    def height(self, height: int):
        self._proto.orthogonal.height.value_nm = height

    @property
    def extension_height(self) -> int:
        return self._proto.orthogonal.extension_height.value_nm

    @extension_height.setter
    def extension_height(self, extension_height: int):
        self._proto.orthogonal.extension_height.value_nm = extension_height

    @property
    def alignment(self) -> base_types_pb2.AxisAlignment.ValueType:
        return self._proto.orthogonal.alignment

    @alignment.setter
    def alignment(self, alignment: base_types_pb2.AxisAlignment.ValueType):
        self._proto.orthogonal.alignment = alignment

class RadialDimension(Dimension):
    def __init__(self, proto: Optional[board_types_pb2.Dimension] = None):
        self._proto = board_types_pb2.Dimension()

        if proto is not None:
            assert proto.WhichOneof("dimension_style") == "radial"
            self._proto.CopyFrom(proto)
        else:
            self._proto.radial.SetInParent()

    def __repr__(self) -> str:
        return (
            f"RadialDimension(center={self.center}, radius_point={self.radius_point}, "
            f"leader_length={self.leader_length})"
        )

    @property
    def center(self) -> Vector2:
        return Vector2(self._proto.radial.center)

    @center.setter
    def center(self, center: Vector2):
        self._proto.radial.center.CopyFrom(center.proto)

    @property
    def radius_point(self) -> Vector2:
        return Vector2(self._proto.radial.radius_point)

    @radius_point.setter
    def radius_point(self, radius_point: Vector2):
        self._proto.radial.radius_point.CopyFrom(radius_point.proto)

    @property
    def leader_length(self) -> int:
        return self._proto.radial.leader_length.value_nm

    @leader_length.setter
    def leader_length(self, leader_length: int):
        self._proto.radial.leader_length.value_nm = leader_length


class LeaderDimension(Dimension):
    def __init__(self, proto: Optional[board_types_pb2.Dimension] = None):
        self._proto = board_types_pb2.Dimension()

        if proto is not None:
            assert proto.WhichOneof("dimension_style") == "leader"
            self._proto.CopyFrom(proto)
        else:
            self._proto.leader.SetInParent()

    def __repr__(self) -> str:
        return (
            f"LeaderDimension(start={self.start}, end={self.end}, "
            f"border_style={self.border_style})"
        )

    @property
    def start(self) -> Vector2:
        return Vector2(self._proto.leader.start)

    @start.setter
    def start(self, start: Vector2):
        self._proto.leader.start.CopyFrom(start.proto)

    @property
    def end(self) -> Vector2:
        return Vector2(self._proto.leader.end)

    @end.setter
    def end(self, end: Vector2):
        self._proto.leader.end.CopyFrom(end.proto)

    @property
    def border_style(self) -> board_types_pb2.DimensionTextBorderStyle.ValueType:
        return self._proto.leader.border_style

    @border_style.setter
    def border_style(self, border_style: board_types_pb2.DimensionTextBorderStyle.ValueType):
        self._proto.leader.border_style = border_style


class CenterDimension(Dimension):
    def __init__(self, proto: Optional[board_types_pb2.Dimension] = None):
        self._proto = board_types_pb2.Dimension()

        if proto is not None:
            assert proto.WhichOneof("dimension_style") == "center"
            self._proto.CopyFrom(proto)
        else:
            self._proto.center.SetInParent()

    def __repr__(self) -> str:
        return f"CenterDimension(center={self.center}, end={self.end})"

    @property
    def center(self) -> Vector2:
        return Vector2(self._proto.center.center)

    @center.setter
    def center(self, center: Vector2):
        self._proto.center.center.CopyFrom(center.proto)

    @property
    def end(self) -> Vector2:
        return Vector2(self._proto.center.end)

    @end.setter
    def end(self, end: Vector2):
        self._proto.center.end.CopyFrom(end.proto)


def to_concrete_dimension(dimension: Dimension) -> Optional[Dimension]:
    cls = {
        "aligned": AlignedDimension,
        "orthogonal": OrthogonalDimension,
        "radial": RadialDimension,
        "leader": LeaderDimension,
        "center": CenterDimension,
        None: None,
    }.get(dimension._proto.WhichOneof("dimension_style"), None)

    return cls(dimension._proto) if cls is not None else None


class BoardEditorAppearanceSettings(Wrapper):
    def __init__(
        self,
        proto: Optional[board_commands_pb2.BoardEditorAppearanceSettings] = None,
        proto_ref: Optional[board_commands_pb2.BoardEditorAppearanceSettings] = None,
    ):
        self._proto = (
            proto_ref
            if proto_ref is not None
            else board_commands_pb2.BoardEditorAppearanceSettings()
        )

        if proto is not None:
            self._proto.CopyFrom(proto)

    @property
    def inactive_layer_display(self) -> board_commands_pb2.InactiveLayerDisplayMode.ValueType:
        """How layers other than the active (selected) layer are displayed"""
        return self._proto.inactive_layer_display

    @inactive_layer_display.setter
    def inactive_layer_display(self, mode: board_commands_pb2.InactiveLayerDisplayMode.ValueType):
        self._proto.inactive_layer_display = mode

    @property
    def net_color_display(self) -> board_commands_pb2.NetColorDisplayMode.ValueType:
        """Whether to apply net and netclass colors to copper items and ratsnest lines"""
        return self._proto.net_color_display

    @net_color_display.setter
    def net_color_display(self, mode: board_commands_pb2.NetColorDisplayMode.ValueType):
        self._proto.net_color_display = mode

    @property
    def board_flip(self) -> board_commands_pb2.BoardFlipMode.ValueType:
        """Whether or not the board view is flipped (mirrored around the X axis)"""
        return self._proto.board_flip

    @board_flip.setter
    def board_flip(self, mode: board_commands_pb2.BoardFlipMode.ValueType):
        self._proto.board_flip = mode

    @property
    def ratsnest_display(self) -> board_commands_pb2.RatsnestDisplayMode.ValueType:
        """Whether or not ratsnest lines are drawn to hidden layers"""
        return self._proto.ratsnest_display

    @ratsnest_display.setter
    def ratsnest_display(self, mode: board_commands_pb2.RatsnestDisplayMode.ValueType):
        self._proto.ratsnest_display = mode


_proto_to_object: Dict[type[Message], type[Wrapper]] = {
    board_types_pb2.Arc: ArcTrack,
    board_types_pb2.BoardGraphicShape: BoardShape,
    board_types_pb2.BoardText: BoardText,
    board_types_pb2.BoardTextBox: BoardTextBox,
    board_types_pb2.Dimension: Dimension,
    board_types_pb2.Field: Field,
    board_types_pb2.Footprint3DModel: Footprint3DModel,
    board_types_pb2.FootprintInstance: FootprintInstance,
    board_types_pb2.Net: Net,
    board_types_pb2.Pad: Pad,
    board_types_pb2.Track: Track,
    board_types_pb2.Via: Via,
    board_types_pb2.Zone: Zone,
}


def unwrap(message: Any) -> Wrapper:
    concrete = unpack_any(message)
    wrapper = _proto_to_object.get(type(concrete), None)
    assert wrapper is not None
    return wrapper(proto=concrete)
