import numpy as np
from make_music import SR, midi, piano, pad, bass, violin, softkick, reverb, master, add, write_wav
DUR=122.62; n=int(DUR*SR)
dL=np.zeros(n,np.float32); dR=np.zeros(n,np.float32)   # dry bus (melody, kick)
wL=np.zeros(n,np.float32); wR=np.zeros(n,np.float32)   # wet bus (pad, bass, violin)
def d(s,at,pan=0.5): add(dL,s*(1-pan),at); add(dR,s*pan,at)
def w(s,at,pan=0.5): add(wL,s*(1-pan),at); add(wR,s*pan,at)
def padrange(notes,t0,t1,amp): w(pad([midi(m) for m in notes],t1-t0+0.6,amp),t0,0.5)

# TITLE + bed
padrange([53,57,60],0.2,7,0.045)
# HOOK — a warm F, the Keeper
d(piano(midi(53),5,0.16),7,0.45)
# GATHERING — F major bed warming; each note: soft call, answer, then the seat 'ring'
padrange([53,57,60],7,78,0.05)
w(bass(midi(41),72,0.08),7,0.5)
seats=[(28,55),(42,57),(58,60),(72,62)]   # G A C D land here (abs time, pitch)
for S,P in seats:
    d(piano(midi(P),2.2,0.10),S-4,0.4)    # Keeper calls
    d(piano(midi(P),2.0,0.09),S-2,0.6)    # the note answers
    d(piano(midi(P),3.2,0.18),S,0.5)      # it takes its step (the ring)
# soft breathing kick, sparse, building gently through the gather
t=30.0
while t<76:
    d(softkick(0.18+0.06*min(1,(t-30)/40)),t,0.5)
    if t>50: d(softkick(0.12),t+1.5,0.5)
    t+=3.0
# WINTER — the danger: high trembling violin (defence), tense pad, kick gone
padrange([50,53,56,60],78,105,0.05)      # tense cluster (D F Ab C)
w(bass(midi(38),27,0.07),78,0.5)          # low tense drone
for at,vn in [(80,76),(86,79),(91,77),(96,81),(100,79)]:
    w(violin(midi(vn),6,0.15,tremolo=0.7),at,0.55+0.1*((at//5)%2))
d(piano(midi(53),4,0.08),90,0.4)          # keeper, hushed, unresolved
# DROP — near silence, one lonely low note
d(piano(midi(41),6,0.12),105,0.5)
# RESOLUTION — the four call, F comes home, the pentatonic run, violin reconciled
for i,P in enumerate([55,57,60,62]): d(piano(midi(P),2.4,0.12),109+i*0.7,0.5)
d(piano(midi(53),7,0.20),112,0.5)         # F, the root, home
run=[53,55,57,60,62,60,57,55,53]
for i,P in enumerate(run): d(piano(midi(P),1.8,0.13),113+i*0.34,0.5)
padrange([53,57,60,65],110,122,0.05)      # warm Fmaj bed returns
w(violin(midi(69),6,0.13,vib=1.3),113,0.6)   # violin sings, reconciled (A)
w(violin(midi(72),6,0.12,vib=1.4),114.5,0.45) # C
w(bass(midi(41),10,0.08),112,0.5)
t=112.0
while t<120: d(softkick(0.16),t,0.5); t+=1.5

dry=np.stack([reverb(dL,mix=0.45),reverb(dR,mix=0.45)],1)
wet=np.stack([reverb(wL,mix=1.0),reverb(wR,mix=1.0)],1)
mix=master(dry*0.92+wet)
fi,fo=int(0.6*SR),int(4*SR); mix[:fi]*=np.linspace(0,1,fi)[:,None]; mix[-fo:]*=np.linspace(1,0,fo)[:,None]
write_wav('ep4_score.wav',mix); print('scored',DUR)
