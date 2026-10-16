import type {Risk, SavedItem} from './types'
export const riskLabels: Record<Risk,string> = {high:'Risiko tinggi',medium:'Risiko sedang',valuable:'Bernilai',low:'Risiko rendah',unknown:'Tanya pengelola'}
export const riskDescriptions: Record<Risk,string> = {high:'Pusat pengelolaan khusus',medium:'Pengolah logam',valuable:'Pemrosesan bernilai ekonomi',low:'Daur ulang atau pakai ulang',unknown:'Perlu pemeriksaan pengelola'}
export const riskOrder: Risk[] = ['high','medium','valuable','low','unknown']
export function itemRisk(item:SavedItem): Risk|'unrecognized' {return item.result.status==='out_of_reference' || !item.result.info ? 'unrecognized' : item.result.info.risk_level}
export function summarize(items:SavedItem[]) {
  const counts:Record<Risk|'unrecognized',number> = {high:0,medium:0,valuable:0,low:0,unknown:0,unrecognized:0}
  items.forEach(item => counts[itemRisk(item)]++)
  return counts
}
export const rupiah = (n:number) => new Intl.NumberFormat('id-ID',{style:'currency',currency:'IDR',maximumFractionDigits:0}).format(n)
