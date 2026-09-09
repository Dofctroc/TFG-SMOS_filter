class MASK_LIMIT():
    def __init__(self, fstart: float, fstop: float, value_dB: float, upper_lower: str, loss_type: str):
        self.fstart = fstart
        self.fstop = fstop
        self.value_dB = value_dB
        self.upper_lower = upper_lower
        self.loss_type = loss_type

class MASK():
    def __init__(self, name: str, limits: list[MASK_LIMIT]):
        self.name = name
        self.limits = limits

class FrequencyPlan():
    def __init__(self, fstart: float, fstop: float, Nsteps: int):
        self.fstart = fstart
        self.fstop = fstop
        self.Nsteps = Nsteps

class FilterResponse():
    def __init__(self, Y=None, f=None):
        self.Y = Y
        self.f = f

class BVD():
    def __init__(self, name: str, c0: float, cp: float, ca: float, la: float, fs: float, fp: float, 
                 cadd_shu: float, ladd_shu: float, cadd_ser: float, ladd_ser: float, ladd_ground: float, 
                 rs: float, rp: float, ql: float, qc: float, qa: float, Y=None, f=None):
        self.name = name
        self.c0 = c0
        self.cp = cp
        self.ca = ca
        self.la = la
        self.fs = fs
        self.fp = fp
        self.cadd_shu = cadd_shu
        self.ladd_shu = ladd_shu
        self.cadd_ser = cadd_ser
        self.ladd_ser = ladd_ser
        self.ladd_ground = ladd_ground
        self.rs = rs
        self.rp = rp
        self.ql = ql
        self.qc = qc
        self.qa = qa
        self.Y = Y
        self.f = f

class COMconstants():
    def __init__(self, k11, k12, vp, eps_r):
        self.k11 = k11
        self.k12 = k12
        self.vp = vp
        self.eps_r = eps_r

class COM():
    def __init__(self, name: str = None, d: float = None, dR: float = None, Ap: float = None, 
        digitsN: int = None, digitsNR: int = None, fs: float = None, fp: float = None, 
        alpha: float = None, alpha_n: float = None, Ct: float = None, Y = None, f = None,
        constants: COMconstants = None):
        self.name = name
        self.d = d
        self.dR = dR
        self.Ap = Ap
        self.digitsN = digitsN
        self.digitsNR = digitsNR
        self.alpha = alpha
        self.alpha_n = alpha_n
        self.Ct = Ct
        self.fs = fs
        self.fp = fp
        self.Y = Y
        self.f = f
        self.constants = constants