// Original, locally synthesized arcade soundtrack. No media downloads or autoplay.
// Browser/OS speech voices may require the voice provider's own network service.
export function createAudio(env=globalThis){
 let ctx=null,master=null,musicBus=null,effectBus=null,timer=null,nextBeat=0,beat=0;
 let active=false,disposed=false,music=true,effects=true,speech=true,utterance=null;
 const voices=new Set();
 const notes=[220,0,329.63,0,293.66,0,261.63,329.63,196,0,293.66,0,261.63,0,246.94,293.66];
 function hasSpeech(){return !!(env.speechSynthesis&&env.SpeechSynthesisUtterance);}
 function busVolume(value){try{musicBus?.gain.setTargetAtTime(value,ctx.currentTime,.08);}catch{}}
 function tone(freq,at,length,volume,type='sine',endFreq=null,bus=effectBus){
  if(!ctx||!bus||ctx.state!=='running'||voices.size>64)return;
  let osc,gain;
  try{
   osc=ctx.createOscillator();gain=ctx.createGain();osc.type=type;
   osc.frequency.setValueAtTime(freq,at);
   if(endFreq!==null)osc.frequency.exponentialRampToValueAtTime(Math.max(15,endFreq),at+length);
   gain.gain.setValueAtTime(.0001,at);gain.gain.exponentialRampToValueAtTime(Math.max(.0002,volume),at+.012);
   gain.gain.exponentialRampToValueAtTime(.0001,at+length);
   osc.connect(gain);gain.connect(bus);voices.add(osc);
   osc.onended=()=>{voices.delete(osc);try{osc.disconnect();gain.disconnect();}catch{}};
   osc.start(at);osc.stop(at+length+.03);
  }catch{if(osc)voices.delete(osc);try{osc?.disconnect();gain?.disconnect();}catch{}}
 }
 function schedule(){
  if(!active||!music||!ctx||ctx.state!=='running')return;
  if(nextBeat<ctx.currentTime-.4)nextBeat=ctx.currentTime+.02;
  let guard=0;
  while(nextBeat<ctx.currentTime+.55&&guard++<8){
   const n=notes[beat%notes.length];
   if(n)tone(n,nextBeat,.23,.19,'triangle',null,musicBus);
   if(beat%4===0)tone(beat%16<8?110:98,nextBeat,.35,.22,'sine',null,musicBus);
   if(beat%2===0)tone(950,nextBeat,.035,.035,'triangle',350,musicBus);
   beat++;nextBeat+=.3;
  }
 }
 function stopMusic(){
  if(timer!==null){env.clearInterval?.(timer);timer=null;}
  // Gain mutes already-scheduled notes immediately while their short envelopes end.
  busVolume(.0001);
 }
 function startMusic(){
  if(!active||!music||!ctx||ctx.state!=='running'||timer!==null)return;
  nextBeat=ctx.currentTime+.025;busVolume(utterance?.12:.55);schedule();
  timer=env.setInterval?.(schedule,160)??null;
 }
 async function unlock(){
  if(disposed)return false;active=true;
  try{
   if(!ctx){const C=env.AudioContext||env.webkitAudioContext;if(!C)return false;ctx=new C();master=ctx.createGain();master.gain.value=.20;master.connect(ctx.destination);musicBus=ctx.createGain();musicBus.gain.value=.55;musicBus.connect(master);effectBus=ctx.createGain();effectBus.gain.value=.8;effectBus.connect(master);}
   if(ctx.state==='suspended')await ctx.resume();
   if(!active||disposed)return false;
   startMusic();return ctx.state==='running';
  }catch{return false;}
 }
 function setMusic(value){music=!!value;if(music)startMusic();else stopMusic();}
 function setEffects(value){effects=!!value;}
 function cancelSpeech(){
  if(utterance){utterance.onend=null;utterance.onerror=null;utterance=null;}
  try{env.speechSynthesis?.cancel();}catch{}
  busVolume(music?.55:.0001);
 }
 function setSpeech(value){speech=!!value;if(!speech)cancelSpeech();}
 function speak(text){
  if(!active||!speech||!hasSpeech()||typeof text!=='string'||!text.trim())return false;
  try{
   cancelSpeech();const u=new env.SpeechSynthesisUtterance(text.slice(0,240));utterance=u;
   u.lang='en-US';u.rate=.85;u.pitch=1;u.volume=.85;
   const v=(env.speechSynthesis.getVoices?.()||[]).find(v=>v.lang?.toLowerCase()==='en-us')||(env.speechSynthesis.getVoices?.()||[]).find(v=>/^en\b/i.test(v.lang));if(v)u.voice=v;
   busVolume(music?.12:.0001);
   const ended=()=>{if(utterance===u){utterance=null;busVolume(music?.55:.0001);}};
   u.onend=ended;u.onerror=ended;env.speechSynthesis.speak(u);return true;
  }catch{utterance=null;busVolume(music?.55:.0001);return false;}
 }
 function effect(name){
  if(!active||!effects||!ctx||ctx.state!=='running')return;
  const t=ctx.currentTime;
  switch(name){
   case 'laser':tone(1800,t,.15,.4,'sawtooth',160);break;
   case 'missile':tone(120,t,.28,.35,'sawtooth',850);tone(70,t,.35,.15,'triangle',35);break;
   case 'explosion':tone(100,t,.45,.5,'sawtooth',18);tone(173,t+.018,.28,.3,'square',27);tone(720,t,.12,.12,'triangle',43);break;
   case 'load':tone(523.25,t,.12,.27,'sine');tone(783.99,t+.12,.18,.23,'sine');break;
   case 'error':tone(170,t,.14,.2,'triangle',100);break;
  }
 }
 function stop(){
  active=false;stopMusic();cancelSpeech();
  for(const osc of voices){try{osc.stop();osc.disconnect();}catch{}}voices.clear();
 }
 async function dispose(){if(disposed)return;stop();disposed=true;try{await ctx?.close();}catch{}ctx=null;}
 return {unlock,setMusic,setEffects,setSpeech,speak,effect,stop,dispose,hasSpeech};
}
