import numpy as np
from scipy.optimize import least_squares
import copy

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

class COM():
    def __init__(self, name: str = None, d: float = None, Ap: float = None, 
        digitsN: int = None, digitsNR: int = None, fs: float = None, fp: float = None, 
        alpha: float = None, alpha_n: float = None, Ct: float = None, Y = None, f = None):
        self.name = name
        self.d = d
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

class FilterResponse():
    def __init__(self, Y=None, f=None):
        self.Y = Y
        self.f = f

K11_REAL = -82053.9
K11 = -82053.9 - 1j*450
K12 = 59340.0

DIGITS_NR = 40
NR = DIGITS_NR*2
DIGITS_NIDT_MIN = 100
DIGITS_NIDT_MAX = 400
AP_MIN = 10
AP_MAX = 30

VP = 3741.8
EPS_R = 39.56
EPS_0 = 8.854e-12
DUTY = 0.55

Z0_PRIMA = 1
R_SHUNT = 4e5
R_SERIE = 0.1

N_POINTS_GRAPH = int(1e4)
R_TERMG = 50

def create_list_BVD(parametersBVD: dict) -> list[BVD]:
    list_BVD: list[BVD] = []

    startBVD_type = parametersBVD["typeseriesshunt_ini"]

    cp = parametersBVD["cp_vals"]       #float[]
    ca = parametersBVD["ca_vals"]       #float[]
    la = parametersBVD["la_vals"]       #float[]

    ladd_ser = parametersBVD["ladd_ser_vals"]           #float[]
    ladd_shu = parametersBVD["ladd_shu_vals"]           #float[]
    cadd_ser = parametersBVD["cadd_ser_vals"]           #float[]
    cadd_shu = parametersBVD["cadd_shu_vals"]           #float[]
    ladd_ground = parametersBVD["ladd_ground_vals"]     #float[]

    rs = float(parametersBVD["rs"])
    rp = float(parametersBVD["rp"])
    ql = float(parametersBVD["ql"])
    qc = float(parametersBVD["qc"])
    qa = float(parametersBVD["qa"])

    currentType = startBVD_type
    
    for i in range(len(cp)):
        name = f"BVD_{currentType}_{i+1}"

        c0 = cp[i] + ca[i]
        fs = 1/(2 * np.pi * np.sqrt(la[i] * ca[i]))
        fp = 1/(2 * np.pi)*np.sqrt((cp[i]+ca[i])/(cp[i]*ca[i]*la[i]))

        bvd = BVD(name=name, c0=c0, cp=cp[i], ca=ca[i], la=la[i], fs=fs, fp=fp, 
                  ladd_ser=ladd_ser[i], ladd_shu=ladd_shu[i], cadd_ser=cadd_ser[i], 
                  cadd_shu=cadd_shu[i], ladd_ground=ladd_ground[i], 
                  rs=rs, rp=rp, ql=ql, qc=qc, qa=qa)
        bvd = compute_admitance_BVD(bvd, parametersBVD)
        
        currentType = "shunt" if currentType == "series" else "series"
        list_BVD.append(bvd)

    return list_BVD

def compute_admitance_BVD(bvd: BVD, parameters: dict) -> BVD:

    fstart = float(parameters["fstart1"])
    fstop = float(parameters["fstop1"])
    npoints = max(int(parameters["npoints1"]), N_POINTS_GRAPH)

    f = np.linspace(fstart, fstop, npoints)

    z_la = Zl(f, bvd.la)
    z_cp = Zc(f, bvd.cp)
    z_ca = Zc(f, bvd.ca)
    z_ra = 2*np.pi*f*bvd.la/bvd.qa

    z_cadd_shu = Zc(f, bvd.cadd_shu, bvd.qc)
    z_ladd_shu = Zl(f, bvd.ladd_shu, bvd.ql)

    z_cadd_ser = Zc(f, bvd.cadd_ser, bvd.qc)
    z_ladd_ser = Zl(f, bvd.ladd_ser, bvd.ql)

    z_ladd_gnd = Zl(f, bvd.ladd_ground, bvd.ql)

    y_core = (1/z_cadd_shu + 1/(bvd.rp + z_cp) + 1/(z_la + z_ca + z_ra) + 1/z_ladd_shu )
    z_core = 1/y_core

    Z_bvd = bvd.rs + z_core + z_ladd_ser + z_cadd_ser + z_ladd_gnd
    Y_bvd = np.nan_to_num(1/Z_bvd)

    bvd.Y = Y_bvd
    bvd.f = f

    return bvd

def compute_list_COM(list_BVD: list[BVD], parameters: dict) -> list[COM]:
    list_COM: list[COM] = []

    for bvd in list_BVD:
        com = COM()
        # 1) ============================= CÁLCULO DEL PITCH =============================
        # Cálculo constantes de entrada y pitch directo
        com.d = compute_pitch_COM(bvd)

        # 2) ======================== CÁLCULO DE APERTURE Y N_IDT ========================
        # Cálculo constantes de entrada
        com.Ct = bvd.cp
        com = compute_Nidt_Aperture_COM(com)

        # 3) ============================= CÁLCULO DE ALPHA =============================
        com = compute_alpha_COM(bvd, com) # Primera aproximació

        com.name = bvd.name.replace("BVD", "COM")
        com = compute_admitance_COM(com, parameters)
        
        list_COM.append(com)

        # Recalcul pitch
        # Rescalar apertura amb ratio fora banda (correcció en apertura (aquesta) o en nombre de digits)
            # Si limita Ap, recalculem Ct i a partir d'aquesta calculem digitsN limitant Ap
            # digitsN ha de quedar enter (rodonejar a l'alça o a la baixa) -> recalculo l'apertura 
        # Recalcul alpha (a partir de l'alpha normalitzada i el canvi de l'apertura o a partir d'alpha fent el coeficient d'arrels d'apertura)
    
    # list_COM = reajuste_pitch(list_BVD, list_COM, parameters)
    # list_COM = reajuste_alpha(list_BVD, list_COM, parameters)
    # list_COM = reajuste_digitsNR(list_BVD, list_COM, parameters)

    return list_COM

def compute_pitch_COM(bvd: BVD) -> float:
    k_fs = (2*np.pi*bvd.fs)/VP
    p =  np.pi / (k_fs+K11_REAL+K12)
    return p

def compute_Nidt_Aperture_COM(com: COM) -> COM:
    # Primer cálculo de Aperture
    Ct = com.Ct
    lambda0 = 2*com.d
    Nidt = 150

    const = EPS_R * EPS_0 *np.exp(0.71866*np.tan(DUTY-0.5))

    Ap = Ct / (Nidt * const) / lambda0
    
    # Comprobación de los límites para Ap y ajuste de Nidt
    if Ap > AP_MAX:
        Ap = AP_MAX
        Nidt = Ct / (Ap * const) / lambda0
        Nidt = round(Nidt)
        
        # Recalculamos la Apertura debido al redondeo de Nidt
        Ap = Ct / (Nidt * const) / lambda0

    elif Ap < AP_MIN:
        Ap = AP_MIN
        Nidt = Ct / (Ap * const) / lambda0
        Nidt = round(Nidt)
        
        # Recalculamos la Apertura debido al redondeo de Nidt
        Ap = Ct / (Nidt * const) / lambda0

    com.Ap = Ap
    com.digitsN = Nidt*2
    com.digitsNR = DIGITS_NR

    return com

def compute_alpha_COM(bvd: BVD, com: COM) -> COM:
    # Cálculo constantes de entrada
    Ct = com.Ct
    k0 = np.pi/com.d
    lambda0 = 2*com.d
    Nidt = com.digitsN/2
    Ap = com.Ap
    k_fp = (2*np.pi*bvd.fp)/VP

    delta = k_fp - k0
    beta = np.sqrt((delta+K11)**2 - K12**2)
    pe = (beta-delta-K11)/K12

    theta = beta*Nidt*lambda0/2
    theta_R = beta*NR*lambda0/2

    z_0 = (1-pe)/(1+pe)*Z0_PRIMA
    z_0R = (1+pe)/(1-pe)*Z0_PRIMA
    z_inR = 1 / ( 1 / (1j*z_0R*np.tan(theta_R)+Z0_PRIMA) + 1j*np.sin(2*theta_R)/z_0R) + 1j*z_0R*np.tan(theta_R)

    # Variables para la resolución de la ecuación cuadrática
    A = 1j*2*np.pi*bvd.fp*Ct
    B = 1 / (1j*2*theta*z_0)
    C = (1j*z_0R*np.tan(theta) + z_inR) / 2 + z_0R / (1j*np.sin(2*theta))
    D = (Z0_PRIMA / (2*theta*z_0))**2

    # Resolución de la ecuación cuadrática
    # Nos quedamos solo con la solución positiva
    phi = abs(np.sqrt(-1/R_SHUNT - A / (B + D/C)))

    # Cálculo final de alpha
    alpha = phi / (2*Nidt*lambda0*np.sqrt(Z0_PRIMA))
    alpha_n = alpha / np.sqrt(Ap)

    # Assign values
    com.alpha = alpha
    com.alpha_n = alpha_n

    return com

def compute_admitance_COM(com: COM, parameters: dict) -> COM:
    # Sweep parameters
    fstart = float(parameters["fstart1"])
    fstop = float(parameters["fstop1"])
    npoints = max(int(parameters["npoints1"]), N_POINTS_GRAPH)

    f = np.linspace(fstart, fstop, npoints)

    # Calculamos la admitancia para cado bloque COM
    k = (2*np.pi*f)/VP
    lambda0 = 2*com.d
    k0 = np.pi/com.d
    Nidt = com.digitsN/2
    Nrefl = com.digitsNR/2

    delta = k - k0
    beta = np.sqrt((delta+K11)**2 - K12**2)
    pe = (beta-delta-K11)/K12

    theta = beta*Nidt*lambda0/2
    theta_R = beta*Nrefl*lambda0/2

    z_0 = (1-pe)/(1+pe)*Z0_PRIMA
    z_0R = (1+pe)/(1-pe)*Z0_PRIMA
    z_inR = 1 / ( 1 / (1j*z_0R*np.tan(theta_R)+Z0_PRIMA) + 1j*np.sin(2*theta_R)/z_0R) + 1j*z_0R*np.tan(theta_R)

    # Variables para la resolución de la ecuación cuadrática
    A = 1j*2*np.pi*f*com.Ct
    B = 1 / (1j*2*theta*z_0)
    C = (1j*z_0R*np.tan(theta) + z_inR) / 2 + z_0R / (1j*np.sin(2*theta))
    D = (Z0_PRIMA / (2*theta*z_0))**2
    phi = 2*com.alpha*Nidt*lambda0*np.sqrt(Z0_PRIMA)

    Z_com = (R_SERIE + 1 / (1/R_SHUNT + A + B*phi**2 + D/C * phi**2))
    Y_com = 1 / Z_com

    # Asignar variables
    com.Y = Y_com
    com.f = f

    Y_com_dB = 20 * np.log10(np.abs(Y_com) + 1e-20)
    com.fs = f[np.argmax(Y_com_dB)]
    com.fp = f[np.argmin(Y_com_dB)]

    return com

def reajuste_pitch(list_BVD: list[BVD], list_COM: list[COM], parameters: dict) -> list[COM]:
    for bvd, com in zip(list_BVD, list_COM):
        f_correction = bvd.fs / com.fs 
        com.d = com.d / f_correction

        com = compute_admitance_COM(com, parameters)

    return list_COM

def reajuste_alpha(list_BVD: list[BVD], list_COM: list[COM], parameters: dict) -> list[COM]:
    for bvd, com in zip(list_BVD, list_COM):
        f_correction = bvd.fp / com.fp 
        com.alpha_n = com.alpha_n / f_correction
        com.alpha = com.alpha_n * np.sqrt(com.Ap)

        com = compute_admitance_COM(com, parameters)

    return list_COM

def reajuste_digitsNR(list_BVD: list[BVD], list_COM: list[COM], parameters: dict) -> list[COM]:
    for bvd, com in zip(list_BVD, list_COM):
        # 1. Definimos la máscara para frecuencias <= fs
        mask = bvd.f <= bvd.fs
        f_target = bvd.f[mask]
        Y_target = bvd.Y[mask]

        # 2. Definimos la función de error que usará least_squares
        def objetivo(nr_val):
            # Actualizamos el valor de NR en el objeto COM (nr_val viene como array de 1 elemento)
            com.digitsNR = nr_val[0]
            
            # Recalculamos la admitancia con el nuevo NR
            # Asumimos que esta función actualiza com.Y internamente
            com_actualizado = compute_admitance_COM(com, parameters)
            
            # El error es la diferencia entre la curva real y la calculada
            # Solo comparamos en el rango de frecuencias definido por la máscara
            error = Y_target - com_actualizado.Y[mask]
            
            # Si Y es compleja (admitancia), devolvemos el valor absoluto o separamos real/imag
            # least_squares requiere valores reales, así que devolvemos la magnitud del error
            return np.abs(error)

        # 3. Ejecutamos la optimización
        # x0 es el valor inicial de NR que ya tiene el objeto
        res = least_squares(
            objetivo, 
            x0=[com.digitsNR], 
            bounds=(10, 100)  # Opcional: evita que NR sea negativo si no tiene sentido físico
        )

        # 4. Aplicamos el resultado final optimizado al objeto
        com.digitsNR = round(res.x[0])
        com = compute_admitance_COM(com, parameters) # Cálculo final definitivo

    return list_COM

def duplicate_resonators(list_BVD: list[BVD], list_COM: list[COM], parameters: dict) -> tuple[list[BVD], list[COM]]:
    # Dejaremos la apertura tal cual la teniamos
    # Doblaremos en serie si    Nidt > max
    # Doblaremos en paralelo si Nidt < min
    list_BVD_duplicados: list[BVD] = []
    list_COM_duplicados: list[COM] = []

    idx = 0
    for com in list_COM:
        bvd_base = list_BVD[idx]
        if com.digitsN < DIGITS_NIDT_MIN:
            # Duplicamos en serie
            # Duplicamos o dividimos los parametros del BVD
            bvd_1 = copy.copy(bvd_base)
            bvd_1.cp = bvd_base.cp*2
            bvd_1.ca = bvd_base.ca*2
            bvd_1.la = bvd_base.la/2
            bvd_1.rs = bvd_base.rs/2
            bvd_1.rp = bvd_base.rp/2
            bvd_1.c0 = bvd_1.cp + bvd_1.ca
            bvd_1.fs = 1/(2 * np.pi * np.sqrt(bvd_1.la * bvd_1.ca))
            bvd_1.fp = 1/(2 * np.pi)*np.sqrt((bvd_1.cp+bvd_1.ca)/(bvd_1.cp*bvd_1.ca*bvd_1.la))
            bvd_2 = copy.copy(bvd_1)

            bvd_1.name = bvd_base.name + "_1s"
            bvd_2.name = bvd_base.name + "_2s"

            bvd_1 = compute_admitance_BVD(bvd_1, parameters)
            bvd_2 = compute_admitance_BVD(bvd_2, parameters)
            list_BVD_duplicados.extend([bvd_1, bvd_2])

            # Duplicamos el valor de DigitsActiveIDT del COM
            com_base = list_COM[idx]
            com_1 = copy.copy(com_base)
            com_1.digitsN = round(com_base.digitsN*2)
            com_2 = copy.copy(com_1)

            com_1.name = com_base.name + "_1s"
            com_2.name = com_base.name + "_2s"

            com_1 = compute_admitance_COM(com_1, parameters)
            com_2 = compute_admitance_COM(com_2, parameters)
            list_COM_duplicados.extend([com_1, com_2])

        elif com.digitsN > DIGITS_NIDT_MAX:
            # Duplicamos en paralelo
            bvd_1 = copy.copy(list_BVD[idx])
            bvd_1.cp = bvd_base.cp/2
            bvd_1.ca = bvd_base.ca/2
            bvd_1.la = bvd_base.la*2
            bvd_1.rs = bvd_base.rs*2
            bvd_1.rp = bvd_base.rp*2
            bvd_1.c0 = bvd_1.cp + bvd_1.ca
            bvd_1.fs = 1/(2 * np.pi * np.sqrt(bvd_1.la * bvd_1.ca))
            bvd_1.fp = 1/(2 * np.pi)*np.sqrt((bvd_1.cp+bvd_1.ca)/(bvd_1.cp*bvd_1.ca*bvd_1.la))
            bvd_2 = copy.copy(bvd_1)

            bvd_1.name = bvd_base.name + "_1p"
            bvd_2.name = bvd_base.name + "_2p"

            bvd_1 = compute_admitance_BVD(bvd_1, parameters)
            bvd_2 = compute_admitance_BVD(bvd_2, parameters)
            list_BVD_duplicados.extend([bvd_1, bvd_2])

            # Dividimosc el valor de DigitsActiveIDT del COM
            com_base = list_COM[idx]
            com_1 = copy.copy(com_base)
            com_1.digitsN = round(com_base.digitsN/2)
            com_2 = copy.copy(com_1)

            com_1.name = com_base.name + "_1p"
            com_2.name = com_base.name + "_2p"

            com_1 = compute_admitance_COM(com_1, parameters)
            com_2 = compute_admitance_COM(com_2, parameters)
            list_COM_duplicados.extend([com_1, com_2])
        
        else:
            list_BVD_duplicados.append(bvd_base)
            list_COM_duplicados.append(com)

        idx += 1

    return list_BVD_duplicados, list_COM_duplicados
        
def Zc(f: list[complex], C: float, Q=None):
    if C == 0:
        return np.full_like(f, np.inf, dtype=complex)
    jw = 1j * 2 * np.pi * f
    if Q is None:
        return 1/(jw*C)
    return 1 / (jw*C + 1/(Q/2*np.pi*f*C))

def Zl(f: list[complex], L: float, Q=None):
    if L == 0:
        return np.zeros_like(f, dtype=complex)
    jw = 1j * 2 * np.pi * f
    if Q is None:
        return jw*L
    return jw*L + 2*np.pi*f*L/Q













# ======================================== DEPRECATED ========================================
def compute_filter_admitance(list: list, parameters: dict) -> FilterResponse:
    # General Parameter
    start_type = parameters["typeseriesshunt_ini"]
    order = int(parameters["norder_ini"])

    # Matching Network parameters
    matching_network_type = parameters["matching_network"]
    mntype1 = parameters["mntype1"]
    input_l = float(parameters["input_l"])
    lfini1 = float(parameters["lfini1"])
    lfini2 = float(parameters["lfini2"])
    cfini1 = float(parameters["cfini1"])
    cfini2 = float(parameters["cfini2"])

    # End element type
    if order % 2 == 0:
        end_type = "shunt" if start_type == "series" else "series"
    else:
        end_type = "series" if start_type == "series" else "shunt"

    # Sweep parameters
    fstart = float(parameters["fstart1"])
    fstop = float(parameters["fstop1"])
    npoints = max(int(parameters["npoints1"]), N_POINTS_GRAPH)

    f = np.linspace(fstart, fstop, npoints)
    Ytot = np.zeros(len(f), dtype=complex)
    Ztot = np.zeros(len(f), dtype=complex)
    Zend = np.zeros(len(f), dtype=complex)

    # Primero el final, depende de si es LC(s-p), CL(p-s) o L(s) o L(p)
    if matching_network_type == "0.0":
        # Output matching network is a single inductance
        if end_type == "series":
            Zend = 1 / (1/(Zl(f,lfini2)) + 1/(R_TERMG))
        else:
            Zend = Zl(f,lfini2) + R_TERMG
    else:
        # Output has a LC matching network
        if mntype1 == "s":
            # Matching Network LC(s-p)
            Zend = Zl(f,lfini1) + 1 / (1/(Zc(f,cfini2)) + 1/(R_TERMG))
        else:
            # Matching Network CL(p-s)
            Zend = 1 / (1/(Zc(f,cfini1)) + 1/(Zl(f,lfini2) + R_TERMG))

    Zeq = Zend
    
    # A continuación, depende de si el último elemento es shunt o serie (si es serie se suma con Zend, si es shunt se suma en paralelo)
    element_type = end_type
    for element in reversed(list):
        if element_type == "series":
            # Sumamos en serie Zeq y Zelement
            Zeq = Zeq + 1/element.Y
        else:
            # Sumamos en paralelo Zeq y Zelement
            Zeq = 1 / (1/Zeq + element.Y)

        element_type = "series" if element_type == "shunt" else "shunt"

    # Finalmente añadimos la impedancia de la bobina en la entrada
    if input_l < 1e-12: 
        # Si es casi 0, ignoramos la bobina (asumimos que no hay matching shunt)
        Ztot = Zeq
    else:
        if start_type == "series":
            # Bobina shunt, sumamos en paralelo
            Ztot = 1 / (1/Zeq + 1/Zl(f, input_l))
        else:
            # Bobina serie, sumamos en serie
            Ztot = Zeq + Zl(f, input_l)

    Ytot = 1/Ztot

    return FilterResponse(Ytot, f)
    

