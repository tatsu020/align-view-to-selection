import bmesh
import math
from mathutils import Matrix, Vector


def jacobi_eigensystem_symmetric_3x3(matrix):
    """Return sorted eigenvalues/eigenvectors for a symmetric 3x3 matrix."""
    a = [[float(matrix[r][c]) for c in range(3)] for r in range(3)]
    v = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]

    for _ in range(50):
        pairs = ((0, 1), (0, 2), (1, 2))
        p, q = max(pairs, key=lambda pair: abs(a[pair[0]][pair[1]]))
        if abs(a[p][q]) < 1.0e-13:
            break

        phi = 0.5 * math.atan2(2.0 * a[p][q], a[q][q] - a[p][p])
        c, s = math.cos(phi), math.sin(phi)

        app, aqq, apq = a[p][p], a[q][q], a[p][q]
        a[p][p] = c*c*app - 2.0*s*c*apq + s*s*aqq
        a[q][q] = s*s*app + 2.0*s*c*apq + c*c*aqq
        a[p][q] = a[q][p] = 0.0

        for r in range(3):
            if r in (p, q):
                continue
            arp, arq = a[r][p], a[r][q]
            a[r][p] = a[p][r] = c * arp - s * arq
            a[r][q] = a[q][r] = s * arp + c * arq

        for r in range(3):
            vrp, vrq = v[r][p], v[r][q]
            v[r][p] = c * vrp - s * vrq
            v[r][q] = s * vrp + c * vrq

    raw_values = [a[0][0], a[1][1], a[2][2]]
    raw_vectors = [
        Vector((v[0][i], v[1][i], v[2][i])).normalized()
        for i in range(3)
    ]
    order = sorted(range(3), key=lambda i: raw_values[i])
    return (
        [raw_values[i] for i in order],
        [raw_vectors[i] for i in order],
    )


def best_fit_plane(points):
    """Fit a plane to point positions using PCA."""
    if len(points) < 3:
        return None, None, "Select at least 3 vertices."

    center = sum(points, Vector((0.0, 0.0, 0.0))) / len(points)

    xx = xy = xz = yy = yz = zz = 0.0
    for point in points:
        d = point - center
        xx += d.x * d.x
        xy += d.x * d.y
        xz += d.x * d.z
        yy += d.y * d.y
        yz += d.y * d.z
        zz += d.z * d.z

    covariance = (
        (xx, xy, xz),
        (xy, yy, yz),
        (xz, yz, zz),
    )
    values, vectors = jacobi_eigensystem_symmetric_3x3(covariance)

    largest = max(abs(values[2]), 1.0e-20)
    if abs(values[1]) / largest < 1.0e-8:
        return None, None, (
            "Selection is nearly a straight line; plane direction is ambiguous."
        )

    return center, vectors[0].normalized(), None


def selected_world_points(context):
    """Collect selected vertex positions from every mesh in Edit Mode."""
    points = []
    objects = [obj for obj in context.objects_in_mode if obj.type == 'MESH']

    if not objects and context.edit_object and context.edit_object.type == 'MESH':
        objects = [context.edit_object]

    for obj in objects:
        bm = bmesh.from_edit_mesh(obj.data)
        world = obj.matrix_world
        points.extend(world @ vertex.co for vertex in bm.verts if vertex.select)

    return points


def project_to_plane(vector, normal):
    projected = vector - normal * vector.dot(normal)
    if projected.length < 1.0e-10:
        return None
    return projected.normalized()


def quaternion_from_screen_axes(screen_x, screen_y, screen_z):
    matrix = Matrix((
        (screen_x.x, screen_y.x, screen_z.x),
        (screen_x.y, screen_y.y, screen_z.y),
        (screen_x.z, screen_y.z, screen_z.z),
    ))
    return matrix.to_quaternion().normalized()


def choose_normal_side(rv3d, normal):
    """Choose the plane side already facing the viewer."""
    current_view_z = rv3d.view_rotation @ Vector((0.0, 0.0, 1.0))
    if normal.dot(current_view_z) < 0.0:
        normal = -normal
    return normal.normalized()


def rotation_preserve_roll(rv3d, normal):
    """Snap the view direction while keeping current screen-up where possible."""
    current_up = rv3d.view_rotation @ Vector((0.0, 1.0, 0.0))
    current_right = rv3d.view_rotation @ Vector((1.0, 0.0, 0.0))

    up = project_to_plane(current_up, normal)

    if up is None:
        right = project_to_plane(current_right, normal)
        if right is not None:
            up = normal.cross(right).normalized()

    if up is None:
        up = project_to_plane(Vector((0.0, 0.0, 1.0)), normal)
    if up is None:
        up = project_to_plane(Vector((0.0, 1.0, 0.0)), normal)
    if up is None:
        up = Vector((0.0, 1.0, 0.0))

    right = up.cross(normal).normalized()
    up = normal.cross(right).normalized()
    return quaternion_from_screen_axes(right, up, normal)
