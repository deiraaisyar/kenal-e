import {describe,it,expect,vi} from 'vitest'
import {renderToStaticMarkup} from 'react-dom/server'
import type {Info,Price} from './types'
vi.mock('./store',()=>({useDrawer:vi.fn()}))
import {Handling,PriceView} from './App'

const info:Info={weee:'Campuran',risk_level:'unknown',bag:'white',hazard_note:'Periksa jenis barang.',do:['Simpan komponen dalam wadah.'],dont:['Jangan membakar.'],assessable:false,verified:false}
describe('audited guidance and price views',()=>{
  it('shows authored initial handling even when identity/risk is unresolved',()=>{
    const html=renderToStaticMarkup(<Handling info={info}/>)
    expect(html).toContain('Simpan komponen dalam wadah.')
    expect(html).toContain('Jangan membakar.')
    expect(html).not.toContain('Panduan khusus belum tersedia')
  })
  it('displays the price scope without opening details and omits research-web label',()=>{
    const price:Price={mode:'ranges',whole:null,scrap:{min:7000,max:10000,unit:'kg',currency:'IDR',accessed_on:'2026-10-18',note:'Catatan sumber',scope:'Konfirmasikan grade paket baterai.',requires_confirmation:[],sources:[{title:'Sumber',url:'https://example.com'}]}}
    const html=renderToStaticMarkup(<PriceView price={price} info={info}/>)
    expect(html.indexOf('Konfirmasikan grade paket baterai.')).toBeLessThan(html.indexOf('<details'))
    expect(html).not.toContain('HASIL RISET WEB')
    expect(html).toContain('kg')
  })
  it('explains unavailable estimates instead of inventing a zero value',()=>{
    const html=renderToStaticMarkup(<PriceView price={{mode:'none',unavailable_reason:'Jenis masih campuran.'}} info={info}/>)
    expect(html).toContain('Jenis masih campuran.')
    expect(html).not.toContain('Rp0')
  })
})
