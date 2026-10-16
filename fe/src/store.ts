import {create} from 'zustand'
import {createJSONStorage,persist} from 'zustand/middleware'
import {get,set,del} from 'idb-keyval'
import type {Analysis,SavedItem} from './types'
type Drawer = {items:SavedItem[];hydrated:boolean;storageError:boolean;add:(item:SavedItem)=>void;remove:(id:string)=>void;update:(id:string,result:Analysis)=>void;clear:()=>void;setHydrated:()=>void}
export const useDrawer = create<Drawer>()(persist((set)=>({items:[],hydrated:false,storageError:false,
  add:item=>set(s=>({items:[...s.items,item]})),remove:id=>set(s=>({items:s.items.filter(i=>i.id!==id)})),
  update:(id,result)=>set(s=>({items:s.items.map(i=>i.id===id?{...i,result}:i)})),clear:()=>set({items:[]}),setHydrated:()=>set({hydrated:true}),
}),{name:'eokay-laci-v1',storage:createJSONStorage(()=>({getItem:async k=>(await get<string>(k))??null,setItem:async(k,v)=>{try{await set(k,v)}catch{if(!useDrawer.getState().storageError)useDrawer.setState({storageError:true})}},removeItem:async k=>{await del(k)}})),partialize:state=>({items:state.items}),onRehydrateStorage:()=> (_state,error)=>{useDrawer.setState({hydrated:true,storageError:!!error})}}))
