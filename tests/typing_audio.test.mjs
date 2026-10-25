import test from 'node:test';
import assert from 'node:assert/strict';
import {createAudio} from '../typing/audio.mjs';
function mock(){
 const calls={tones:0,stops:0,say:[],cancel:0,resume:0,interval:0,cleared:0};
 const param=()=>({value:0,setValueAtTime(){},exponentialRampToValueAtTime(){},linearRampToValueAtTime(){},setTargetAtTime(){},cancelScheduledValues(){}});
 class Context{constructor(){this.currentTime=0;this.state='suspended';this.destination={};}createGain(){return {gain:param(),connect(){},disconnect(){}};}createOscillator(){calls.tones++;return {frequency:param(),connect(){},disconnect(){},start(){},stop(){calls.stops++;},type:'sine'};}async resume(){calls.resume++;this.state='running';}async close(){this.state='closed';}}
 class Utterance{constructor(text){this.text=text;}}
 const env={AudioContext:Context,SpeechSynthesisUtterance:Utterance,speechSynthesis:{getVoices:()=>[{lang:'en-US',name:'English'}],speak:u=>calls.say.push(u),cancel:()=>calls.cancel++},setInterval:()=>{calls.interval++;return 7;},clearInterval:()=>calls.cleared++};
 return {calls,env};
}
test('safe in browser without either audio capability',async()=>{const a=createAudio({});assert.equal(a.hasSpeech(),false);assert.equal(await a.unlock(),false);a.speak('moon');a.effect('explosion');a.stop();await a.dispose();});
test('no autoplay; gesture unlock starts a quiet looping music schedule',async()=>{const {env,calls}=mock();const a=createAudio(env);assert.equal(calls.tones,0);assert.equal(calls.interval,0);assert.equal(await a.unlock(),true);assert.equal(calls.resume,1);assert.ok(calls.tones>0);assert.equal(calls.interval,1);a.stop();assert.ok(calls.cleared>0);await a.dispose();});
test('independent music effects and speech toggles; no voices after stop',async()=>{const {env,calls}=mock();const a=createAudio(env);a.setMusic(false);await a.unlock();assert.equal(calls.interval,0);const before=calls.tones;a.effect('laser');assert.ok(calls.tones>before);a.setEffects(false);const muted=calls.tones;a.effect('explosion');assert.equal(calls.tones,muted);a.setMusic(true);assert.equal(calls.interval,1);a.speak('moon');assert.equal(calls.say.at(-1).text,'moon');assert.equal(calls.say.at(-1).lang,'en-US');a.setSpeech(false);a.speak('sun');assert.equal(calls.say.length,1);a.stop();a.effect('laser');a.speak('star');assert.equal(calls.say.length,1);await a.dispose();});
test('fresh utterances cancel backlog; old end events cannot interfere',async()=>{const {env,calls}=mock();const a=createAudio(env);await a.unlock();a.speak('one');const oldEnd=calls.say[0].onend;a.speak('two');assert.equal(calls.say.length,2);assert.ok(calls.cancel>=2);assert.equal(calls.say[0].onend,null);oldEnd();calls.say[1].onerror();a.stop();await a.dispose();});
test('every attack effect uses finite short-lived oscillator nodes',async()=>{const {env,calls}=mock();const a=createAudio(env);a.setMusic(false);await a.unlock();for(const e of ['laser','missile','explosion','load','error'])a.effect(e);assert.ok(calls.tones>=5);assert.ok(calls.stops>=calls.tones);await a.dispose();});
test('unlock failure is non-fatal and speech can still work',async()=>{const {env,calls}=mock();env.AudioContext=class {constructor(){throw new Error('blocked');}};const a=createAudio(env);assert.equal(await a.unlock(),false);a.speak('hello');assert.equal(calls.say.length,1);await a.dispose();});
