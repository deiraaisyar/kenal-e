import {describe,expect,it} from 'vitest'
import {itemRisk,summarize} from './domain'
import type {SavedItem,Risk} from './types'
const item=(risk:Risk|null):SavedItem=>({id:crypto.randomUUID(),createdAt:'2026-10-16',photo:null,result:{status:risk?'borderline':'out_of_reference',macro:risk?{id:13,name:'Barang'}:null,sub:null,info:risk?{risk_level:risk,bag:'green',verified:false,assessable:true,weee:'',hazard_note:'',do:[],dont:[]}:null,price:null,similar:[],taxonomy_version:'progress-21',disclaimer:''}})
describe('Cek Laci report',()=>{
  it('keeps counts consistent for eight items and handles unknown separately',()=>{
    const rows=[item('high'),item('high'),item('medium'),item('valuable'),item('valuable'),item('low'),item('unknown'),item(null)]
    const counts=summarize(rows)
    expect(Object.values(counts).reduce((a,b)=>a+b,0)).toBe(8)
    expect(counts).toEqual({high:2,medium:1,valuable:2,low:1,unknown:1,unrecognized:1})
    expect(itemRisk(rows[7])).toBe('unrecognized')
  })
  it('moves manually corrected items into the new group',()=>{
    const row=item('valuable');if(row.result.info)row.result.info.risk_level='high'
    expect(summarize([row]).high).toBe(1)
    expect(summarize([row]).valuable).toBe(0)
  })
})
