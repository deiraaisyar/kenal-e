import {useState} from 'react'
import {ChevronDown,SlidersHorizontal,X} from 'lucide-react'
import type {Category} from './types'
import {categoryFacets,emptyFilters,facetKeys,facetLabel,facetOptions,facetTitles,toggleFacet} from './catalogFilters'
import type {CatalogSelection,FacetKey} from './catalogFilters'

const riskDetails:Record<string,string>={high:'Mudah terbakar',medium:'Logam berat/timbal',valuable:'Logam berharga',low:'Logam/plastik umum'}

export function CatalogFilters({value,onChange,count}:{value:CatalogSelection;onChange:(value:CatalogSelection)=>void;count?:number}) {
  const [dimension,setDimension]=useState<FacetKey>('groups')
  const selected=facetKeys.flatMap(key=>value[key].map(id=>({key,id})))
  return <section className="catalog-filter-section" aria-label="Penyaringan katalog">
    <details className="catalog-filters">
      <summary><SlidersHorizontal size={17}/><span>Filter barang</span>{selected.length>0&&<b>{selected.length}</b>}<ChevronDown size={17}/></summary>
      <div className="catalog-filter-content">
        <div className="facet-switch" role="group" aria-label="Pilih jenis filter">{facetKeys.map(key=><button type="button" key={key} aria-pressed={dimension===key} onClick={()=>setDimension(key)}>{facetTitles[key]}{value[key].length>0&&<span>{value[key].length}</span>}</button>)}</div>
        <p className="filter-hint">Bisa pilih lebih dari satu.</p>
        <div className="facet-options" role="group" aria-label={'Filter '+facetTitles[dimension].toLowerCase()}>
          <button type="button" aria-pressed={!value[dimension].length} onClick={()=>onChange({...value,[dimension]:[]})}>Semua</button>
          {Object.entries(facetOptions[dimension]).map(([id,label])=><button type="button" key={id} aria-pressed={value[dimension].includes(id)} onClick={()=>onChange(toggleFacet(value,dimension,id))}>{label}{dimension==='risks'&&riskDetails[id]&&<small>{riskDetails[id]}</small>}</button>)}
        </div>
      </div>
    </details>
    {selected.length>0&&<div className="active-facets" aria-label="Filter aktif">{selected.map(({key,id})=><button type="button" key={key+id} onClick={()=>onChange(toggleFacet(value,key,id))} aria-label={'Hapus filter '+facetLabel(key,id)}>{key==='sizes'?'Ukuran: ':''}{facetLabel(key,id)}<X size={13}/></button>)}</div>}
    <div className="catalog-filter-summary"><span role="status">{count===undefined?'Memuat barang…':`${count} jenis barang${selected.length?' cocok':' tersedia'}`}</span>{selected.length>0&&<button type="button" onClick={()=>onChange(emptyFilters())}>Hapus semua filter</button>}</div>
  </section>
}

export function CategoryLabels({category}:{category:Category}) {
  const facets=categoryFacets(category)
  const labels=[...facets.groups.map(id=>facetLabel('groups',id)),...facets.sizes.map(id=>id==='unidentified'?'Ukuran belum teridentifikasi':'Ukuran '+facetLabel('sizes',id).toLocaleLowerCase('id'))]
  return labels.length?<span className="category-facet-labels">{labels.map(label=><span key={label}>{label}</span>)}</span>:null
}
export function CategoryRisks({category}:{category:Category}) {
  return <span className="category-risks">{categoryFacets(category).risks.map(risk=><span className={'risk-badge '+risk} key={risk}><span/>{facetLabel('risks',risk)}</span>)}</span>
}
