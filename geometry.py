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

from __future__ import annotations

from typing import Optional, Union
import math
from kipy.proto.common import types
from kipy.util import from_mm
from kipy.wrapper import Wrapper

import sys
import math

class Vector2(Wrapper):
    """Wraps a kiapi.common.types.Vector2, aka VECTOR2I"""
    def __init__(self, proto: Optional[types.Vector2] = None):
        self._proto = types.Vector2()

        if proto is not None:
            self._proto.CopyFrom(proto)

    def __repr__(self):
        return f"Vector2({self.x}, {self.y})"

    @classmethod
    def from_xy(cls, x_nm: int, y_nm: int):
        """Initialize Vector2 with x and y values in nanometers"""
        proto = types.Vector2()
        proto.x_nm = x_nm
        proto.y_nm = y_nm
        return cls(proto)

    @classmethod
    def from_xy_mm(cls, x_mm: int, y_mm: int):
        """Initialize Vector2 with x and y values in mm

        .. versionadded:: 0.3.0"""
        proto = types.Vector2()
        proto.x_nm = from_mm(x_mm)
        proto.y_nm = from_mm(y_mm)
        return cls(proto)

    @property
    def x(self) -> int:
        return self._proto.x_nm

    @x.setter
    def x(self, val: int):
        self._proto.x_nm = val

    @property
    def y(self) -> int:
        return self._proto.y_nm

    @y.setter
    def y(self, val: int):
        self._proto.y_nm = val

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        if isinstance(other, Vector2):
            return self.x == other.x and self.y == other.y
        return NotImplemented

    def __add__(self, other: Vector2) -> Vector2:
        r = Vector2(self._proto)
        r.x += other.x
        r.y += other.y
        return r

    def __sub__(self, other: Vector2) -> Vector2:
        r = Vector2(self._proto)
        r.x -= other.x
        r.y -= other.y
        return r

    def __neg__(self) -> Vector2:
        r = Vector2(self._proto)
        r.x = -r.x
        r.y = -r.y
        return r

    def __mul__(self, scalar: float) -> Vector2:
        r = Vector2(self._proto)
        r.x = int(float(r.x) * scalar)
        r.y = int(float(r.y) * scalar)
        return r

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def angle(self) -> float:
        """Returns the angle (direction) of the vector in radians"""
        return math.atan2(self.y, self.x)

    def angle_degrees(self) -> float:
        """Returns the angle (direction) of the vector in degrees

        .. versionadded:: 0.3.0
        """
        return math.degrees(self.angle())

    def rotate(self, angle: Angle, center: Vector2) -> Vector2:
        """Rotates the vector in-place by an angle in degrees around a center point

        :param angle: The angle to rotate by
        :param center: The center point to rotate around
        :return: The rotated vector

        .. versionadded:: 0.4.0
        """
        pt_x = self.x - center.x
        pt_y = self.y - center.y
        rotation = normalize_angle_radians(angle.to_radians())

        sin_angle = math.sin(rotation)
        cos_angle = math.cos(rotation)

        self.x = int(pt_y * sin_angle + pt_x * cos_angle) + center.x
        self.y = int(pt_y * cos_angle - pt_x * sin_angle) + center.y

        return self

class Vector3D(Wrapper):
    """Wraps a kiapi.common.types.Vector3D"""
    def __init__(self, proto: Optional[types.Vector3D] = None):
        self._proto = types.Vector3D()

        if proto is not None:
            self._proto.CopyFrom(proto)

    def __repr__(self):
        return f"Vector3D({self.x}, {self.y}, {self.z})"

    @classmethod
    def from_xyz(cls, x_nm: float, y_nm: float, z_nm: float):
        """Initialize Vector3D with x, y, and z values in nanometers"""
        proto = types.Vector3D()
        proto.x_nm = x_nm
        proto.y_nm = y_nm
        proto.z_nm = z_nm
        return cls(proto)

    @property
    def x(self) -> float:
        return self._proto.x_nm

    @x.setter
    def x(self, val: float):
        self._proto.x_nm = val

    @property
    def y(self) -> float:
        return self._proto.y_nm

    @y.setter
    def y(self, val: float):
        self._proto.y_nm = val

    @property
    def z(self) -> float:
        return self._proto.z_nm

    @z.setter
    def z(self, val: float):
        self._proto.z_nm = val

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def __eq__(self, other):
        if isinstance(other, Vector3D):
            return self.x == other.x and self.y == other.y and self.z == other.z
        return NotImplemented

    def __add__(self, other: Vector3D) -> Vector3D:
        r = Vector3D(self._proto)
        r.x += other.x
        r.y += other.y
        r.z += other.z
        return r

    def __sub__(self, other: Vector3D) -> Vector3D:
        r = Vector3D(self._proto)
        r.x -= other.x
        r.y -= other.y
        r.z -= other.z
        return r

    def __neg__(self) -> Vector3D:
        r = Vector3D(self._proto)
        r.x = -r.x
        r.y = -r.y
        r.z = -r.z
        return r

    def __mul__(self, scalar: float) -> Vector3D:
        r = Vector3D(self._proto)
        r.x = r.x * scalar
        r.y = r.y * scalar
        r.z = r.z * scalar
        return r

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

class Box2:
    def __init__(
        self,
        pos_proto: Optional[types.Vector2] = None,
        size_proto: Optional[types.Vector2] = None,
    ):
        self._pos_proto = types.Vector2()
        self._size_proto = types.Vector2()

        if pos_proto is not None:
            self._pos_proto.CopyFrom(pos_proto)

        if size_proto is not None:
            self._size_proto.CopyFrom(size_proto)

    def __repr__(self):
        return f"Box2(pos={self.pos}, size={self.size})"

    @classmethod
    def from_xywh(cls, x_nm: int, y_nm: int, w_nm: int, h_nm: int):
        pos = Vector2.from_xy(x_nm, y_nm)
        size = Vector2.from_xy(w_nm, h_nm)
        return cls(pos._proto, size._proto)

    @classmethod
    def from_pos_size(cls, pos: Vector2, size: Vector2):
        return cls(pos._proto, size._proto)

    @classmethod
    def from_proto( cls, other: types.Box2):
        return cls(other.position, other.size)

    @property
    def pos(self) -> Vector2:
        return Vector2(self._pos_proto)

    @property
    def size(self) -> Vector2:
        return Vector2(self._size_proto)

    def move(self, delta: Vector2):
        self._pos_proto.x_nm += delta.x
        self._pos_proto.y_nm += delta.y

    def center(self) -> Vector2:
        center_x = self._pos_proto.x_nm + self._size_proto.x_nm // 2
        center_y = self._pos_proto.y_nm + self._size_proto.y_nm // 2
        return Vector2.from_xy(center_x, center_y)

    def merge(self, other: Union[Vector2, Box2]):
        if isinstance(other, Vector2):
            min_x = min(self.pos.x, other.x)
            min_y = min(self.pos.y, other.y)
            max_x = max(self.pos.x + self.size.x, other.x)
            max_y = max(self.pos.y + self.size.y, other.y)
        else:
            min_x = min(self.pos.x, other.pos.x)
            min_y = min(self.pos.y, other.pos.y)
            max_x = max(self.pos.x + self.size.x, other.pos.x + other.size.x)
            max_y = max(self.pos.y + self.size.y, other.pos.y + other.size.y)

        self._pos_proto.x_nm = min_x
        self._pos_proto.y_nm = min_y
        self._size_proto.x_nm = max_x - min_x
        self._size_proto.y_nm = max_y - min_y

    def inflate(self, amount: int):
        new_width = self.size.x + amount
        new_height = self.size.y + amount
        self._pos_proto.x_nm -= (new_width - self.size.x) // 2
        self._pos_proto.y_nm -= (new_height - self.size.y) // 2
        self._size_proto.x_nm = new_width
        self._size_proto.y_nm = new_height

class Angle(Wrapper):
    def __init__(self, proto: Optional[types.Angle] = None):
        self._proto = types.Angle()

        if proto is not None:
            self._proto.CopyFrom(proto)

    def __repr__(self):
        return f"Angle({self.degrees})"

    @classmethod
    def from_degrees(cls, degrees: float):
        """Initialize Angle with a value in degrees"""
        proto = types.Angle()
        proto.value_degrees = degrees
        return cls(proto)

    @property
    def degrees(self) -> float:
        return self._proto.value_degrees

    @degrees.setter
    def degrees(self, val: float):
        self._proto.value_degrees = val

    def __eq__(self, other):
        if isinstance(other, Angle):
            return self.degrees == other.degrees
        return NotImplemented

    def __add__(self, other: Angle) -> Angle:
        return Angle.from_degrees(self.degrees + other.degrees)

    def __sub__(self, other: Angle) -> Angle:
        return Angle.from_degrees(self.degrees - other.degrees)

    def __neg__(self) -> Angle:
        return Angle.from_degrees(-self.degrees)

    def __mul__(self, scalar: float) -> Angle:
        return Angle.from_degrees(self.degrees * scalar)

    def to_radians(self) -> float:
        return math.radians(self.degrees)

    def normalize(self) -> Angle:
        """Normalizes the angle to fall within the range [0, 360)

        .. versionadded:: 0.4.0"""
        while self.degrees < 0.0:
            self.degrees += 360.0

        while self.degrees >= 360.0:
            self.degrees -= 360.0

        return self

    def normalize180(self) -> Angle:
        """Normalizes the angle to fall within the range [-180, 180)

        .. versionadded:: 0.4.0"""
        while self.degrees <= -180.0:
            self.degrees += 360.0

        while self.degrees > 180.0:
            self.degrees -= 360.0

        return self

class ArcStartMidEnd(Wrapper):
    def __init__(
        self,
        proto: Optional[types.ArcStartMidEnd] = None,
        proto_ref: Optional[types.ArcStartMidEnd] = None,
    ):
        self._proto = proto_ref if proto_ref is not None else types.ArcStartMidEnd()

        if proto is not None:
            self._proto.CopyFrom(proto)

    def __repr__(self):
        return f"ArcStartMidEnd(start={self.start}, mid={self.mid}, end={self.end})"

    @property
    def start(self) -> Vector2:
        return Vector2(self._proto.start)

    @start.setter
    def start(self, val: Vector2):
        self._proto.start.CopyFrom(val._proto)

    @property
    def mid(self) -> Vector2:
        return Vector2(self._proto.mid)

    @mid.setter
    def mid(self, val: Vector2):
        self._proto.mid.CopyFrom(val._proto)

    @property
    def end(self) -> Vector2:
        return Vector2(self._proto.end)

    @end.setter
    def end(self, val: Vector2):
        self._proto.end.CopyFrom(val._proto)

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

    def bounding_box(self) -> Box2:
        """Returns the bounding box of the arc -- not calculated by KiCad; may differ from KiCad's"""
        box = Box2()
        box.merge(self.start)
        box.merge(self.end)
        box.merge(self.mid)
        return box

class PolyLineNode(Wrapper):
    def __init__(
        self,
        proto: Optional[types.PolyLineNode] = None,
        proto_ref: Optional[types.PolyLineNode] = None,
    ):
        self._proto = proto_ref if proto_ref is not None else types.PolyLineNode()

        if proto is not None:
            self._proto.CopyFrom(proto)

    @staticmethod
    def from_point(point: Vector2):
        n = PolyLineNode()
        n.point = point
        return n

    @staticmethod
    def from_xy(x: int, y: int):
        n = PolyLineNode()
        n.point = Vector2.from_xy(x, y)
        return n

    def __repr__(self):
        if self.has_point:
            return f"PolyLineNode(point={self.point})"
        elif self.has_arc:
            return f"PolyLineNode(arc={self.arc})"
        return "PolyLineNode()"

    @property
    def has_point(self) -> bool:
        return self._proto.HasField("point")

    @property
    def point(self) -> Vector2:
        return Vector2(self._proto.point)

    @point.setter
    def point(self, val: Vector2):
        self._proto.point.CopyFrom(val._proto)

    @property
    def has_arc(self) -> bool:
        return self._proto.HasField("arc")

    @property
    def arc(self) -> ArcStartMidEnd:
        return ArcStartMidEnd(self._proto.arc)

    @arc.setter
    def arc(self, val: ArcStartMidEnd):
        self._proto.arc.CopyFrom(val._proto)

class PolyLine(Wrapper):
    def __init__(
        self,
        proto: Optional[types.PolyLine] = None,
        proto_ref: Optional[types.PolyLine] = None,
    ):
        self._proto = proto_ref if proto_ref is not None else types.PolyLine()

        if proto is not None:
            self._proto.CopyFrom(proto)

    def __repr__(self):
        return f"PolyLine(nodes={self.nodes}, closed={self.closed})"

    @property
    def nodes(self) -> list[PolyLineNode]:
        return [PolyLineNode(proto_ref=node) for node in self._proto.nodes]

    @property
    def closed(self) -> bool:
        return self._proto.closed

    @closed.setter
    def closed(self, val: bool):
        self._proto.closed = val

    def __iter__(self):
        return iter(self.nodes)

    def __len__(self):
        return len(self.nodes)

    def __getitem__(self, index: int) -> PolyLineNode:
        return self.nodes[index]

    def __setitem__(self, index: int, value: PolyLineNode):
        self._proto.nodes[index].CopyFrom(value._proto)

    def append(self, node: PolyLineNode):
        self._proto.nodes.append(node._proto)

    def insert(self, index: int, node: PolyLineNode):
        self._proto.nodes.insert(index, node._proto)

    def remove(self, node: PolyLineNode):
        self._proto.nodes.remove(node._proto)

    def clear(self):
        self._proto.ClearField("nodes")

    def rotate(self, delta: Angle, center: Vector2):
        for node in self.nodes:
            if node.has_point:
                node.point = node.point.rotate(delta, center)
            elif node.has_arc:
                node.arc.start = node.arc.start.rotate(delta, center)
                node.arc.mid = node.arc.mid.rotate(delta, center)
                node.arc.end = node.arc.end.rotate(delta, center)

class PolygonWithHoles(Wrapper):
    def __init__(
        self,
        proto: Optional[types.PolygonWithHoles] = None,
        proto_ref: Optional[types.PolygonWithHoles] = None,
    ):
        self._proto = proto_ref if proto_ref is not None else types.PolygonWithHoles()

        if proto is not None:
            self._proto.CopyFrom(proto)

    def __repr__(self):
        return f"PolygonWithHoles(outline={self.outline}, holes={self.holes})"

    @property
    def outline(self) -> PolyLine:
        return PolyLine(proto_ref=self._proto.outline)

    @outline.setter
    def outline(self, outline: PolyLine):
        self._proto.outline.CopyFrom(outline._proto)

    @property
    def holes(self) -> list[PolyLine]:
        return [PolyLine(proto_ref=hole) for hole in self._proto.holes]

    def add_hole(self, hole: PolyLine):
        self._proto.holes.append(hole._proto)

    def remove_hole(self, hole: PolyLine):
        self._proto.holes.remove(hole._proto)

    def bounding_box(self) -> Box2:
        if not self.outline.nodes:
            return Box2()

        min_x = math.inf
        min_y = math.inf
        max_x = -math.inf
        max_y = -math.inf

        for node in self.outline:
            if node.has_point:
                min_x = min(min_x, node.point.x)
                min_y = min(min_y, node.point.y)
                max_x = max(max_x, node.point.x)
                max_y = max(max_y, node.point.y)
            elif node.has_arc:
                box = node.arc.bounding_box()
                min_x = min(min_x, box.pos.x)
                min_y = min(min_y, box.pos.y)
                max_x = max(max_x, box.pos.x + box.size.x)
                max_y = max(max_y, box.pos.y + box.size.y)

        return Box2.from_pos_size(
            Vector2.from_xy(int(min_x), int(min_y)),
            Vector2.from_xy(int(max_x - min_x), int(max_y - min_y)),
        )

    def move(self, delta: Vector2):
        for node in self.outline:
            if node.has_point:
                node.point += delta
            elif node.has_arc:
                node.arc.start += delta
                node.arc.mid += delta
                node.arc.end += delta

        for hole in self.holes:
            for node in hole:
                if node.has_point:
                    node.point += delta
                elif node.has_arc:
                    node.arc.start += delta
                    node.arc.mid += delta
                    node.arc.end += delta

    def rotate(self, delta: Angle, center: Optional[Vector2] = None):
        if center is None:
            center = self.bounding_box().center()

        self.outline.rotate(delta, center)

        for hole in self.holes:
            hole.rotate(delta, center)

def arc_center(start: Vector2, mid: Vector2, end: Vector2) -> Optional[Vector2]:
    """
    Calculates the center of the arc.  Uses the same algorithm as KiCad
    The KiCad API preserves the start, middle, and end points of the arc,
    so any other properties such as the center point and angles must be calculated

    :return: The center of the arc, or None if the arc is degenerate
    """

    center = None

    yDelta_21 = mid.y - start.y
    xDelta_21 = mid.x - start.x
    yDelta_32 = end.y - mid.y
    xDelta_32 = end.x - mid.x
    
    if( ( ( xDelta_21 == 0.0 ) and ( yDelta_32 == 0.0 ) ) or ( ( yDelta_21 == 0.0 ) and ( xDelta_32 == 0.0 ) ) ):
        center = Vector2.from_xy(( start.x + end.x ) / 2.0 , ( start.y + end.y ) / 2.0)
        return center
    
    if( xDelta_21 == 0.0 ):
        xDelta_21 = sys.float_info.epsilon

    if( xDelta_32 == 0.0 ):
        xDelta_32 = -sys.float_info.epsilon
    
    aSlope = yDelta_21 / xDelta_21
    bSlope = yDelta_32 / xDelta_32

    daSlope = aSlope * EuclideanNorm((0.5 / yDelta_21),(0.5 / xDelta_21))
    dbSlope = bSlope * EuclideanNorm((0.5 / yDelta_32),(0.5 / xDelta_32))

    if(aSlope == bSlope):
        if(start == end):
            # This is a special case for a 360 degrees arc.  In this case, the center is
            # halfway between the midpoint and either end point.
            center = Vector2.from_xy(( start.x + mid.x ) / 2.0 , ( start.y + mid.y ) / 2.0)
            return center
        else:
            # If the points are colinear, the center is at infinity, so offset
            # the slope by a minimal amount
            # Warning: This will induce a small error in the center location
            aSlope += sys.float_info.epsilon
            bSlope -= sys.float_info.epsilon

    # Prevent divide by zero error
    # a small value is used. std::numeric_limits<double>::epsilon() is too small and
    # generate false results
    if( aSlope == 0.0 ):
        aSlope = 1e-10
    if( bSlope == 0.0 ):
        bSlope = 1e-10

    # What follows is the calculation of the center using the slope of the two lines as well as
    # the propagated error that occurs when rounding to the nearest nanometer.  The error can be
    # ±0.5 units but can add up to multiple nanometers after the full calculation is performed.
    # All variables starting with `d` are the delta of that variable.  This is approximately equal
    # to the standard deviation.
    # We ignore the possible covariance between variables.  We also truncate our series expansion
    # at the first term.  These are reasonable assumptions as the worst-case scenario is that we
    # underestimate the potential uncertainty, which would potentially put us back at the status
    # quo.    
    
    M_SQRT1_2 = 0.707106781186547524401

    abSlopeStartEndY = aSlope * bSlope * ( start.y - end.y )
    dabSlopeStartEndY = abSlopeStartEndY * \
                               math.sqrt( ( daSlope / aSlope * daSlope / aSlope ) \
                                        + ( dbSlope / bSlope * dbSlope / bSlope ) \
                                        + ( M_SQRT1_2 / ( start.y - end.y ) \
                                          * M_SQRT1_2 / ( start.y - end.y ) ) );
    
    bSlopeStartMidX = bSlope * ( start.x + mid.x )
    dbSlopeStartMidX = bSlopeStartMidX * math.sqrt( ( dbSlope / bSlope * dbSlope / bSlope ) \
                                                         + ( M_SQRT1_2 / ( start.x + mid.x ) \
                                                           * M_SQRT1_2 / ( start.x + mid.x ) ) )

    aSlopeMidEndX = aSlope * ( mid.x + end.x )
    daSlopeMidEndX = aSlopeMidEndX * math.sqrt( ( daSlope / aSlope * daSlope / aSlope ) \
                                                     + ( M_SQRT1_2 / ( mid.x + end.x ) \
                                                       * M_SQRT1_2 / ( mid.x + end.x ) ) )

    twiceBASlopeDiff = 2 * ( bSlope - aSlope )
    dtwiceBASlopeDiff = 2 * math.sqrt( dbSlope * dbSlope + daSlope * daSlope )

    centerNumeratorX = abSlopeStartEndY + bSlopeStartMidX - aSlopeMidEndX
    dCenterNumeratorX = math.sqrt( dabSlopeStartEndY * dabSlopeStartEndY
                                       + dbSlopeStartMidX * dbSlopeStartMidX
                                       + daSlopeMidEndX * daSlopeMidEndX )

    centerX = ( abSlopeStartEndY + bSlopeStartMidX - aSlopeMidEndX ) / twiceBASlopeDiff
    dCenterX = centerX * math.sqrt( ( dCenterNumeratorX / centerNumeratorX *
                                             dCenterNumeratorX / centerNumeratorX )
                                         + ( dtwiceBASlopeDiff / twiceBASlopeDiff *
                                             dtwiceBASlopeDiff / twiceBASlopeDiff ) )

    centerNumeratorY = ( ( start.x + mid.x ) / 2.0 - centerX )
    dCenterNumeratorY = math.sqrt( 1.0 / 8.0 + dCenterX * dCenterX )

    centerFirstTerm = centerNumeratorY / aSlope
    dcenterFirstTermY = centerFirstTerm * math.sqrt( \
                                          ( dCenterNumeratorY/ centerNumeratorY * \
                                            dCenterNumeratorY / centerNumeratorY ) \
                                        + ( daSlope / aSlope * daSlope / aSlope ) )

    centerY = centerFirstTerm + ( start.y + mid.y ) / 2.0
    dCenterY = math.sqrt( dcenterFirstTermY * dcenterFirstTermY + 1.0 / 8.0 )

    rounded100CenterX = math.floor( ( centerX + 50.0 ) / 100.0 ) * 100.0
    rounded100CenterY = math.floor( ( centerY + 50.0 ) / 100.0 ) * 100.0
    rounded10CenterX = math.floor( ( centerX + 5.0 ) / 10.0 ) * 10.0
    rounded10CenterY = math.floor( ( centerY + 5.0 ) / 10.0 ) * 10.0

    # The last step is to find the nice, round numbers near our baseline estimate and see if
    # they are within our uncertainty range.  If they are, then we use this round value as the
    # true value.  This is justified because ALL values within the uncertainty range are equally
    # true.  Using a round number will make sure that we are on a multiple of 1mil or 100nm
    # when calculating centers.

    if(abs( rounded100CenterX - centerX ) < dCenterX and \
        abs( rounded100CenterY - centerY ) < dCenterY ):
        center = Vector2.from_xy(int(rounded100CenterX),int(rounded100CenterY))
    elif(abs( rounded10CenterX - centerX ) < dCenterX and \
             abs( rounded10CenterY - centerY ) < dCenterY ):
        center = Vector2.from_xy(int(rounded10CenterX),int(rounded10CenterY))
    else:
        center = Vector2.from_xy(int(centerX),int(centerY))

    return center

def EuclideanNorm(x,y) -> float:
    # 45° are common in KiCad, so we can optimize the calculation
    if(abs(x) == abs(y)):
        return abs(x) * 1.41421356237309504880

    if(x == 0):
        return abs(y)
    if(y == 0):
        return abs(x)

    return math.hypot(x,y)

def arc_radius(start: Vector2, mid: Vector2, end: Vector2) -> float:
    """
    Calculates the radius of the arc.  Uses a different algorithm than KiCad so may have
    slightly different results.  The KiCad API preserves the start, middle, and end points of
    the arc, so any other properties such as the center point and angles must be calculated

    :return: The radius of the arc, or 0 if the arc is degenerate
    """
    # TODO we may want to add an API call to get KiCad to calculate this for us,
    # for situations where matching KiCad's behavior exactly is important
    center = arc_center(start, mid, end)
    if center is None:
        return 0
    return (start - center).length()

def normalize_angle_degrees(angle: float) -> float:
    """Normalizes an angle to fall within the range [0, 360)

    .. versionadded:: 0.3.0"""
    while angle < 0.0:
        angle += 360.0

    while angle >= 360.0:
        angle -= 360.0

    return angle

def normalize_angle_radians(angle: float) -> float:
    """Normalizes an angle to fall within the range [0, 2*pi)

    .. versionadded:: 0.3.0"""
    while angle < 0.0:
        angle += 2 * math.pi

    while angle >= 2 * math.pi:
        angle -= 2 * math.pi

    return angle

def arc_start_angle(start: Vector2, mid: Vector2, end: Vector2) -> Optional[float]:
    """Calculates the arc's starting angle in radians, normalized to [0, 2*pi)

    :return: The starting angle of the arc, or None if the arc is degenerate"""
    center = arc_center(start, mid, end)
    if center is None:
        return None

    return normalize_angle_radians((start - center).angle())

def arc_end_angle(start: Vector2, mid: Vector2, end: Vector2) -> Optional[float]:
    """Calculates the arc's ending angle in radians, normalized to [0, 2*pi)

    :return: The ending angle of the arc, or None if the arc is degenerate"""
    center = arc_center(start, mid, end)
    if center is None:
        return None

    angle = (end - center).angle()

    start_angle = arc_start_angle(start, mid, end)
    assert(start_angle is not None)

    if angle == start_angle:
        angle += 2 * math.pi

    return normalize_angle_radians(angle)

def arc_start_angle_degrees(start: Vector2, mid: Vector2, end: Vector2) -> Optional[float]:
    """Calculates the arc's starting angle in degrees, normalized to [0, 360)

    .. versionadded:: 0.3.0
    """
    center = arc_center(start, mid, end)
    if center is None:
        return None

    return normalize_angle_degrees((start - center).angle_degrees())

def arc_end_angle_degrees(start: Vector2, mid: Vector2, end: Vector2) -> Optional[float]:
    """Calculates the arc's ending angle in degrees, normalized to [0, 360)

    .. versionadded:: 0.3.0
    """
    center = arc_center(start, mid, end)
    if center is None:
        return None

    angle = (end - center).angle_degrees()

    start_angle = arc_start_angle(start, mid, end)
    assert(start_angle is not None)

    if angle == start_angle:
        angle += 360

    return normalize_angle_degrees(angle)
