import numpy as np
from scipy.signal import iirpeak, butter, lfilter
from make_music import SR, midi, piano, pad, bass, reverb, master, add, write_wav

def bp_body(x):
    out=np.zeros_like(x)
    for fc,Q,g in [(280,2.5,1.0),(460,3,0.9),(820,4,0.7),(1300,5,0.55),(2400,7,0.7),(3200,9,0.5)]:
        b,a=iirpeak(fc/(SR/2),Q); out+=g*lfilter(b,a,x)
    return out
def violin(freq,dur,amp=0.16,vib=1.0):
    n=int(dur*SR); t=np.arange(n)/SR; rng=np.random.default_rng(int(freq*7)%9999)
    vd=0.009*vib*np.clip((t-0.12)/0.35,0,1); jit=0.0013*np.convolve(rng.standard_normal(n),np.ones(40)/40,'same')
    ph=2*np.pi*freq*np.cumsum(1+vd*np.sin(2*np.pi*5.6*t)+jit)/SR
    saw=np.zeros(n)
    for k in range(1,min(40,int((SR/2)/max(freq,20)))): saw+=np.sin(k*ph+rng.uniform(0,6.28))/k
    saw/=2.5
    nz=rng.standard_normal(n); nz=nz-np.convolve(nz,np.ones(20)/20,'same')
    y=bp_body(saw+0.10*nz)*0.9+saw*0.25
    atk,rel=int(0.07*SR),int(0.45*SR); e=np.ones(n)*0.85; e[:atk]=np.linspace(0,1,atk)**0.6
    if rel<n: e[-rel:]=np.linspace(0.85,0,rel)
    return (y*e*amp).astype(np.float32)
def softkick(amp=0.26,dur=0.5):
    n=int(dur*SR); t=np.arange(n)/SR; f=80*np.exp(-t*10)+42
    y=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*5); b,a=butter(2,120/(SR/2)); y=lfilter(b,a,y)
    return (y/(np.max(np.abs(y))+1e-9)*amp).astype(np.float32)

# ---- MIX: separate dry (present) and wet (spacious) buses for balance ----
DUR=90.0; n=int(DUR*SR)
dL=np.zeros(n,np.float32); dR=np.zeros(n,np.float32)   # dry: melody + kick (present)
wL=np.zeros(n,np.float32); wR=np.zeros(n,np.float32)   # wet: pad + bass + violin (spacious)
def d(s,at,pan): add(dL,s*(1-pan),at); add(dR,s*pan,at)
def w(s,at,pan): add(wL,s*(1-pan),at); add(wR,s*pan,at)

BAR=3.0
# functional progression with a smooth bass line + voice-led upper voices, cadence to F
chords=[(41,[57,60,65]),(40,[55,60,64]),(50,[53,57,62]),(48,[53,57,60]),
        (46,[53,58,62]),(45,[57,60,65]),(43,[58,62,65]),(48,[55,58,64])]
# melody: antecedent (bars1-4, ends unresolved on A) + consequent (bars5-8, resolves E->F)
melody=[[(0,65,1.2),(1.2,69,1.0),(2.2,72,0.8)],[(0,72,1.4),(1.6,69,1.2)],
        [(0,69,1.2),(1.4,65,1.4)],[(0,67,1.6),(1.6,69,1.4)],
        [(0,70,1.2),(1.2,69,1.2)],[(0,69,1.2),(1.4,65,1.4)],
        [(0,67,1.2),(1.2,65,1.2)],[(0,64,1.0),(1.2,65,2.2)]]
vcounter=[60,64,65,64,62,60,58,60]  # violin lower counter-voice (contrary motion)

# GAINS (balanced): bed low, melody on top, kick soft
G=dict(padA=0.038,bass=0.10,kick=0.24,mel=0.20,acc=0.085,vln=0.14,arp=0.12)

def bar_at(cyc,bi):
    return (cyc*len(chords)+bi)*BAR

SECTIONS=[("intro",[0]),("themeA",[1]),("themeB",[2]),("climax",[3])]  # 4 cycles of 8 bars = ~96... trim
for cyc,sec in [(0,"intro"),(1,"themeA"),(2,"themeB"),(3,"outro")]:
    dyn={"intro":0.7,"themeA":0.9,"themeB":1.0,"outro":0.8}[sec]
    for bi,(broot,voices) in enumerate(chords):
        t0=bar_at(cyc,bi)
        if t0>=DUR-2: break
        # pad (bed) + bass — the harmony, spacious
        w(pad([midi(m) for m in voices],BAR+0.5,G["padA"]*dyn),t0,0.5)
        if sec!="intro": w(bass(midi(broot),BAR+0.2,G["bass"]),t0,0.5)
        # soft kick pulse (themeA/B) on beats 1 & 3
        if sec in("themeA","themeB"):
            d(softkick(G["kick"]),t0,0.5); d(softkick(G["kick"]*0.8),t0+1.5,0.5)
        # melody / arpeggio
        if sec in("themeA","themeB"):
            for off,m,du in melody[bi]:
                d(piano(midi(m),du+1.2,G["mel"]*dyn),t0+off,0.5)
        else:  # intro & outro: gentle chord arpeggio (present but soft)
            for j,m in enumerate(voices):
                d(piano(midi(m+ (12 if sec=='intro' else 0)),2.4,G["arp"]*dyn),t0+j*0.9,0.42+0.08*j)
        # violin counter-voice (themeB) — contrary motion, blended
        if sec=="themeB":
            w(violin(midi(vcounter[bi]),BAR,G["vln"]),t0+0.15,0.6)
# outro cadence: resolve on F, ritard
d(piano(midi(65),6,0.18),DUR-7,0.5); w(pad([midi(53),midi(57),midi(60)],7,0.05),DUR-7,0.5)
d(piano(midi(60),6,0.12),DUR-6.4,0.55)

dry=np.stack([reverb(dL,mix=0.45),reverb(dR,mix=0.45)],1)     # melody: present, light room
wet=np.stack([reverb(wL,mix=1.0),reverb(wR,mix=1.0)],1)       # pads/violin: spacious
mix=master(dry*0.9+wet)
fi,fo=int(1*SR),int(4*SR); mix[:fi]*=np.linspace(0,1,fi)[:,None]; mix[-fo:]*=np.linspace(1,0,fo)[:,None]
write_wav('piece2.wav',mix); print('done')
