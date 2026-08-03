import '@testing-library/jest-dom/vitest';
class MockWebSocket{onmessage:((e:{data:string})=>void)|null=null;close(){} constructor(){}};Object.defineProperty(globalThis,'WebSocket',{value:MockWebSocket,writable:true});Object.defineProperty(globalThis,'confirm',{value:()=>true,writable:true});
