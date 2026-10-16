import {describe,expect,it} from 'vitest'
import {categoryFacets,emptyFilters,matchesCatalog,toggleFacet} from './catalogFilters'
import type {Category} from './types'
const pcb:Category={id:13,name:'Papan sirkuit (PCB)',size:356,risk_level:'valuable',bag:'green',device:'pcb',thumb_url:null,n_sub:1,facets:{groups:['internal','computing'],sizes:['small','medium'],risks:['valuable','medium']}}
describe('catalog multi-label filtering',()=>{
  it('shows everything when all dimensions are cleared',()=>expect(matchesCatalog(pcb,emptyFilters())).toBe(true))
  it('matches any selected label within a dimension, and all selected dimensions',()=>{
    expect(matchesCatalog(pcb,{groups:['media','internal'],sizes:['small'],risks:['medium']})).toBe(true)
    expect(matchesCatalog(pcb,{groups:['internal'],sizes:['large'],risks:['valuable']})).toBe(false)
    expect(matchesCatalog(pcb,{groups:['media'],sizes:[],risks:[]})).toBe(false)
  })
  it('combines filters with trimmed case-insensitive search',()=>{
    expect(matchesCatalog(pcb,emptyFilters(),' PCB ')).toBe(true)
    expect(matchesCatalog(pcb,emptyFilters(),'baterai')).toBe(false)
  })
  it('toggles labels without clearing another dimension and returns to all',()=>{
    const one=toggleFacet({...emptyFilters(),sizes:['small']},'groups','internal')
    expect(one.groups).toEqual(['internal'])
    const cleared=toggleFacet(one,'groups','internal')
    expect(cleared.groups).toEqual([])
    expect(cleared.sizes).toEqual(['small'])
  })
  it('supports older APIs without inventing group or size metadata',()=>{
    const old={...pcb,facets:undefined}
    expect(categoryFacets(old)).toEqual({groups:[],sizes:[],risks:['valuable']})
    expect(matchesCatalog(old,emptyFilters())).toBe(true)
  })
})
