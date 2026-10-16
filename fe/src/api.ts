import type {Analysis,Category,DropPoint} from './types'
// Local development uses the Vite proxy; production connects to Render by default.
const base = (import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? 'https://still-e-okay.onrender.com' : '')).replace(/\/$/,'')
export class ApiError extends Error {constructor(message:string, public code:string){super(message)}}
export const assetUrl = (url:string) => url.startsWith('/api/') ? base+url : url
async function request<T>(path:string, options:RequestInit = {}):Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(()=>controller.abort(),200_000)
  try {
    const res = await fetch(base+path,{...options,signal:controller.signal})
    if(!res.ok) {
      const body = await res.json().catch(()=>null)
      throw new ApiError(body?.error?.message || 'Layanan belum bisa dihubungi.',body?.error?.code || 'unavailable')
    }
    return await res.json()
  } catch(e) {
    if(e instanceof ApiError) throw e
    if(e instanceof DOMException && e.name==='AbortError') throw new ApiError('Analisis terlalu lama. Silakan coba lagi.','timeout')
    throw new ApiError('Periksa koneksi internetmu, lalu coba lagi.','network')
  } finally {clearTimeout(timer)}
}
export const api = {
  catalog:()=>request<Category[]>('/api/taxonomy'),
  category:(id:number)=>request<Category>('/api/taxonomy/'+id),
  analyze:(file:File)=>{const data=new FormData();data.append('image',file);return request<Analysis>('/api/analyze',{method:'POST',body:data})},
  demo:()=>request<Analysis>('/api/demo'),
  health:()=>request<{backend:string;space:string}>('/api/health'),
  drops:(city:string)=>request<DropPoint[]>('/api/drop-points?city='+encodeURIComponent(city)),
}
export async function compressPhoto(file:File):Promise<{file:File;photo:string}> {
  if(!['image/jpeg','image/png','image/webp'].includes(file.type)) throw new Error('Pilih foto JPG, PNG, atau WEBP.')
  if(file.size>25*1024*1024) throw new Error('Foto terlalu besar. Pilih foto di bawah 25 MB.')
  const bitmap = await createImageBitmap(file).catch(()=>{throw new Error('Foto tidak dapat dibuka. Pilih foto lain.')})
  const ratio=Math.min(1,1024/Math.max(bitmap.width,bitmap.height))
  const canvas=document.createElement('canvas');canvas.width=Math.max(1,Math.round(bitmap.width*ratio));canvas.height=Math.max(1,Math.round(bitmap.height*ratio))
  const ctx=canvas.getContext('2d')!;ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(bitmap,0,0,canvas.width,canvas.height);bitmap.close()
  let quality=.8, photo=canvas.toDataURL('image/jpeg',quality)
  while(photo.length>1_300_000 && quality>.4){quality-=.1;photo=canvas.toDataURL('image/jpeg',quality)}
  const blob=await (await fetch(photo)).blob()
  return {file:new File([blob],'foto-barang.jpg',{type:'image/jpeg'}),photo}
}
