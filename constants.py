TENSION_LIMIT = 30
COMPRESSION_LIMIT = -6
ELASTIC_MODULUS = 4000
POISSON = 0.2
GLUE_SHEAR_LIMIT = 2
MATBOARD_SHEAR_LIMIT = 4
BRIDGE_LENGTH = 1200
PI = 3.14159265358979
EQ_TOL = 1e-8

def eq(a: float, b: float, tol: float = EQ_TOL):
    if abs(a - b) < tol:
        return True
    return False