import numpy as np

class BVD():
    def __init__(self, name, c0, cp, ca, la, fs, fp, cadd_shu, ladd_shu, cadd_ser, 
                 ladd_ser, ladd_ground, rs, rp, ql, qc, qa, Y=None, f=None):
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
    def __init__(self, name, d, Ap, N, NR, alpha, alpha_n, Ct, Y=None, f=None):
        self.name = name
        self.d = d
        self.Ap = Ap
        self.N = N
        self.NR = NR
        self.alpha = alpha
        self.alpha_n = alpha_n
        self.Ct = Ct
        self.Y = Y
        self.f = f

K11_REAL = -82053.9
K11 = -82053.9 - 1j*450
K12 = 59340.0

VP = 3741.8
EPS_R = 39.56
EPS_0 = 8.854e-12
DUTY = 0.55

Z0_PRIMA = 1
R_SHUNT = 4e5
R_SERIE = 0.1

NR = 40

def create_list_BVD(parametersBVD: dict) -> list[BVD]:
    """Crea la lista de valores para el bloque BVD a partir de los parámetros leídos."""
    list_BVD: list[BVD] = []

    startBVD_type = parametersBVD["typeseriesshunt_ini"]

    c0 = parametersBVD["c0_vals"]       #float[]
    cp = parametersBVD["cp_vals"]       #float[]
    ca = parametersBVD["ca_vals"]       #float[]
    la = parametersBVD["la_vals"]       #float[]

    fs = parametersBVD["fs_vals"]       #float[]
    fp = parametersBVD["fp_vals"]       #float[]

    ladd_ser = parametersBVD["ladd_ser_vals"]           #float[]
    ladd_shu = parametersBVD["ladd_shu_vals"]           #float[]
    cadd_ser = parametersBVD["cadd_ser_vals"]           #float[]
    cadd_shu = parametersBVD["cadd_shu_vals"]           #float[]
    ladd_ground = parametersBVD["ladd_ground_vals"]     #float[]

    rs = parametersBVD["rs"]
    rp = parametersBVD["rp"]
    ql = parametersBVD["ql"]
    qc = parametersBVD["qc"]
    qa = parametersBVD["qa"]

    currentType = startBVD_type
    
    for i in range(len(c0)):
        name = f"BVD_{currentType}_{i+1}"

        bvd = BVD(name=name, c0=c0[i], cp=cp[i], ca=ca[i], la=la[i], fs=fs[i], fp=fp[i], 
                  ladd_ser=ladd_ser[i], ladd_shu=ladd_shu[i], cadd_ser=cadd_ser[i], 
                  cadd_shu=cadd_shu[i], ladd_ground=ladd_ground[i], 
                  rs=rs, rp=rp, ql=ql, qc=qc, qa=qa)
        
        currentType = "shunt" if currentType == "series" else "series"
        list_BVD.append(bvd)

    return list_BVD

def compute_list_COM(list_BVD: list[BVD]) -> list[COM]:
    """Computa la lista de valores para el bloque COM a partir de los parámetros leídos."""
    list_COM: list[COM] = []

    # Aquí se pueden agregar cálculos adicionales para obtener los parámetros necesarios para el bloque COM
    # Por ejemplo, podríamos calcular la frecuencia de resonancia, la impedancia característica, etc.
    for bvd in list_BVD:
        # 1) ============================= CÁLCULO DEL PITCH =============================
        # Cálculo constantes de entrada y pitch directo
        k_fs = (2*np.pi*bvd.fs)/VP
        p = np.pi / (k_fs+K11_REAL+K12)

        # Cálculo de variables definidas por el pitch
        lambda0 = 2*p
        k0 = np.pi/p

        # 2) ======================== CÁLCULO DE APERTURE Y N_IDT ========================
        # Cálculo constantes de entrada
        Ct = bvd.cp
        Nidt = 150

        # Primer cálculo de Aperture
        Ap = Ct / (Nidt * EPS_R * EPS_0 *np.exp(0.71866*np.tan(DUTY-0.5))) / lambda0
        
        # Comprobación de los límites para Ap y ajuste de Nidt
        if Ap > 30:
            Ap = 30
            Nidt = Ct / (Ap * EPS_R * EPS_0 *np.exp(0.71866*np.tan(DUTY-0.5))) / lambda0
            Nidt = round(Nidt)
            if Nidt > 500 or Nidt < 50:
                print(f"Advertencia: N calculado es {Nidt}, lo cual está fuera del rango recomendado (50-500).")

        elif Ap < 10:
            Ap = 10
            Nidt = Ct / (Ap * EPS_R * EPS_0 *np.exp(0.71866*np.tan(DUTY-0.5))) / lambda0
            Nidt = round(Nidt)
            if Nidt > 500 or Nidt < 50:
                print(f"Advertencia: N calculado es {Nidt}, lo cual está fuera del rango recomendado (50-500).")
            else:
                # Se recalcula Ap debido al redondeo de Nidt
                Ap = Ct / (Nidt * EPS_R * EPS_0 *np.exp(0.71866*np.tan(DUTY-0.5))) / lambda0

        # 3) ============================= CÁLCULO DE ALPHA =============================
        # Cálculo constantes de entrada
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
        phi = abs(np.sqrt(-1/R_SHUNT -A / (B + D/C)))

        # Cálculo final de alpha
        alpha = phi / (2*Nidt*lambda0*np.sqrt(Z0_PRIMA))
        alpha_n = alpha / np.sqrt(Ap)

        # Assign all values to the COM block
        name = bvd.name.replace("BVD", "COM")
        com = COM(name=name, d=p, Ap=Ap, N=Nidt, NR=NR, alpha=alpha, alpha_n=alpha_n, Ct=Ct)
        list_COM.append(com)

    return list_COM

def compute_admitance_COM(list_COM: list[COM], parameters: dict) -> list[COM]:
    # Sweep parameters
    fstart = float(parameters["fstart1"])
    fstop = float(parameters["fstop1"])
    npoints = int(parameters["npoints1"])

    f = np.linspace(fstart, fstop, npoints)

    for com in list_COM:
        # Calculamos la admitancia para cado bloque COM
        k = (2*np.pi*f)/VP
        lambda0 = 2*com.d
        k0 = np.pi/com.d

        delta = k - k0
        beta = np.sqrt((delta+K11)**2 - K12**2)
        pe = (beta-delta-K11)/K12

        theta = beta*com.N*lambda0/2
        theta_R = beta*NR*lambda0/2

        z_0 = (1-pe)/(1+pe)*Z0_PRIMA
        z_0R = (1+pe)/(1-pe)*Z0_PRIMA
        z_inR = 1 / ( 1 / (1j*z_0R*np.tan(theta_R)+Z0_PRIMA) + 1j*np.sin(2*theta_R)/z_0R) + 1j*z_0R*np.tan(theta_R)

        # Variables para la resolución de la ecuación cuadrática
        A = 1j*2*np.pi*f*com.Ct
        B = 1 / (1j*2*theta*z_0)
        C = (1j*z_0R*np.tan(theta) + z_inR) / 2 + z_0R / (1j*np.sin(2*theta))
        D = (Z0_PRIMA / (2*theta*z_0))**2
        phi = 2*com.alpha*com.N*lambda0*np.sqrt(Z0_PRIMA)

        Z_com = (R_SERIE + 1 / (1/R_SHUNT + A + B*phi**2 + D/C * phi**2))
        Y_com = 1 / Z_com

        com.Y = Y_com
        com.f = f

    return list_COM