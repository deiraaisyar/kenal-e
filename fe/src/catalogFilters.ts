import type {Category} from './types'
import {riskLabels} from './domain'

export const facetOptions = {
  groups: {office:'Elektronik Kantor/Cetak',household:'Elektronik Rumah Tangga Besar',computing:'Perangkat Komputasi',media:'Media/Audio-Visual',energy:'Komponen Elektrik/Energi',internal:'Komponen Internal',mixed:'Timbunan/Campuran'},
  sizes: {small:'Kecil',medium:'Sedang',large:'Besar',unidentified:'Tidak Teridentifikasi'},
  risks: riskLabels,
} satisfies Record<string,Record<string,string>>
export type FacetKey = keyof typeof facetOptions
export type CatalogSelection = Record<FacetKey,string[]>
export const facetTitles:Record<FacetKey,string> = {groups:'Jenis barang',sizes:'Ukuran',risks:'Risiko'}
export const emptyFilters = ():CatalogSelection => ({groups:[],sizes:[],risks:[]})
export const facetKeys:FacetKey[] = ['groups','sizes','risks']
export function categoryFacets(category:Category):CatalogSelection {
  // Older deployments still provide risk_level; do not guess missing paper labels.
  return category.facets ?? {groups:[],sizes:[],risks:[category.risk_level]}
}
export function facetLabel(key:FacetKey,id:string) {
  return (facetOptions[key] as Record<string,string>)[id] ?? id
}
export function toggleFacet(filters:CatalogSelection,key:FacetKey,id:string):CatalogSelection {
  return {...filters,[key]:filters[key].includes(id)?filters[key].filter(v=>v!==id):[...filters[key],id]}
}
export function matchesCatalog(category:Category,filters:CatalogSelection,search='') {
  const facets=categoryFacets(category)
  return category.name.toLocaleLowerCase('id').includes(search.trim().toLocaleLowerCase('id')) &&
    facetKeys.every(key=>!filters[key].length || filters[key].some(id=>facets[key].includes(id)))
}
