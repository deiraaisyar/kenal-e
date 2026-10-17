import {useEffect,useLayoutEffect,useRef,useState} from 'react'
import type {ReactNode} from 'react'
import {NavLink,Route,Routes,useLocation,useNavigate} from 'react-router-dom'
import {useQuery} from '@tanstack/react-query'
import {ArrowDownToLine,ArrowLeft,ArrowRight,Camera,Check,ChevronDown,ChevronRight,CircleAlert,ClipboardList,CloudOff,FolderOpen,Grid2X2,House,Image as ImageIcon,Info,LoaderCircle,MapPin,Maximize2,Plus,Search,Shield,SlidersHorizontal,Tag,Trash2,WifiOff,X} from 'lucide-react'
import {toBlob} from 'html-to-image'
import {api,ApiError,assetUrl,compressPhoto} from './api'
import {DeviceArt} from './Artwork'
import DropPoints from './DropPoints'
import {CatalogFilters,CategoryLabels,CategoryRisks} from './CatalogFilters'
import {matchesCatalog,emptyFilters} from './catalogFilters'
import {itemRisk,riskDescriptions,riskLabels,riskOrder,rupiah,summarize} from './domain'
import {useDrawer} from './store'
import type {Analysis,Category,Info as InfoData,Price,PriceEstimate,Risk,SavedItem} from './types'

type Sheet = {kind:'about'|'upload'|'report'|'drops'} | {kind:'category';id:number} | {kind:'photo';src:string;categoryId?:number} | null
type Current = {result:Analysis;photo:string|null;id:string}

function Brand({white=false}:{white?:boolean}) {return <span className={'brand '+(white?'white':'')}><img src={white?'/logo-white.svg':'/logo.svg'} alt=""/><span>Kenal-E<span className="brand-dot">.</span></span></span>}
function RiskBadge({risk}:{risk:Risk|'unrecognized'}) {return <span className={'risk-badge '+risk}><span/>{risk==='unrecognized'?'Belum dikenali':riskLabels[risk]}</span>}
function Empty({icon=<FolderOpen/>,title,children}:{icon?:ReactNode;title:string;children:ReactNode}) {return <div className="empty"><span className="empty-icon">{icon}</span><h2>{title}</h2><div>{children}</div></div>}
function PageHeader({onAbout}:{onAbout:()=>void}) {return <header className="page-header"><Brand/><button className="icon-button" onClick={onAbout} aria-label="Tentang Kenal-E"><Info size={21}/></button></header>}
function ErrorPanel({message,onRetry}:{message:string;onRetry:()=>void}) {return <div className="error-panel" role="alert"><CircleAlert size={21}/><p>{message}</p><button className="text-button" onClick={onRetry}>Coba lagi <ArrowRight size={16}/></button></div>}

export default function App(){
  const navigate=useNavigate(),location=useLocation()
  const [sheet,setSheet]=useState<Sheet>(null),[current,setCurrent]=useState<Current|null>(null)
  const [busy,setBusy]=useState(false),[error,setError]=useState<ApiError|null>(null),[toast,setToast]=useState('')
  const [online,setOnline]=useState(navigator.onLine),[elapsed,setElapsed]=useState(0)
  const fileInput=useRef<HTMLInputElement>(null),cameraInput=useRef<HTMLInputElement>(null),retryFile=useRef<File|null>(null)
  const items=useDrawer(s=>s.items),add=useDrawer(s=>s.add),storageError=useDrawer(s=>s.storageError)
  const catalog=useQuery({queryKey:['catalog'],queryFn:api.catalog})
  const health=useQuery({queryKey:['health'],queryFn:api.health,enabled:busy&&elapsed>=15,refetchInterval:busy?20_000:false,retry:false})
  useEffect(()=>{const yes=()=>setOnline(true),no=()=>setOnline(false);window.addEventListener('online',yes);window.addEventListener('offline',no);return()=>{window.removeEventListener('online',yes);window.removeEventListener('offline',no)}},[])
  useEffect(()=>{if(!busy){setElapsed(0);return}const start=Date.now();const timer=setInterval(()=>setElapsed(Math.floor((Date.now()-start)/1000)),1000);return()=>clearInterval(timer)},[busy])
  useEffect(()=>{if(!toast)return;const timer=setTimeout(()=>setToast(''),3500);return()=>clearTimeout(timer)},[toast])
  useEffect(()=>{document.querySelector('.phone-app')?.scrollTo(0,0);window.scrollTo(0,0)},[location.pathname])

  const notify=(text:string)=>setToast(text)
  async function analyzeFile(file:File){
    if(busy)return
    if(!navigator.onLine){notify('Analisis foto membutuhkan koneksi internet.');return}
    setSheet(null);setError(null);setBusy(true);setCurrent(null);retryFile.current=file;navigate('/hasil')
    try {const processed=await compressPhoto(file);const result=await api.analyze(processed.file);setCurrent({result,photo:processed.photo,id:crypto.randomUUID()})}
    catch(e){setError(e instanceof ApiError?e:new ApiError(e instanceof Error?e.message:'Foto belum bisa diproses.','invalid_image'))}
    finally{setBusy(false)}
  }
  async function demo(){
    if(busy)return
    setSheet(null);setError(null);setBusy(true);setCurrent(null);retryFile.current=null;navigate('/hasil')
    try{setCurrent({result:await api.demo(),photo:null,id:crypto.randomUUID()})}catch(e){setError(e instanceof ApiError?e:new ApiError('Contoh belum bisa dimuat.','unavailable'))}finally{setBusy(false)}
  }
  const addCurrent=()=>{
    if(!current)return
    if(items.some(i=>i.id===current.id)){navigate('/laci');return}
    add({...current,createdAt:new Date().toISOString()});notify('Barang ditambahkan ke Cek Laci');navigate('/laci')
  }
  const upload=()=>setSheet({kind:'upload'})
  const closeSheet=()=>setSheet(active=>active?.kind==='photo'&&active.categoryId!==undefined?{kind:'category',id:active.categoryId}:null)
  const categoryFor=(result:Analysis)=>catalog.data?.find(c=>c.id===result.macro?.id)
  return <div className="app-stage">
    <aside className="desktop-intro"><Brand/><span className="eyebrow"><span/> KENALI. PILAH. SETOR.</span><h1>Yang lama,<br/>punya langkah<br/><em>baru.</em></h1><p>Mulai dari barang yang tersimpan di rumah. Satu foto, satu langkah untuk memilah.</p><div className="intro-stamp"><Shield size={19}/><span>Panduan awal untuk elektronik lama</span></div><span className="intro-footer">Dibuat untuk langkah kecil yang berarti.</span></aside>
    <div className="phone-app">
      {!online&&<div className="offline-banner" role="status"><WifiOff size={16}/> Kamu offline. Cek Laci tetap bisa dibuka.</div>}
      {storageError&&<div className="offline-banner" role="alert"><CircleAlert size={16}/> Penyimpanan perangkat gagal. Simpan rapor sebelum menutup aplikasi.</div>}
      <main id="main-content"><Routes>
        <Route path="/" element={<Home onAbout={()=>setSheet({kind:'about'})} onPhoto={upload} onCamera={()=>cameraInput.current?.click()} onGallery={()=>fileInput.current?.click()} onDemo={demo}/>}/>
        <Route path="/hasil" element={<Result current={current} busy={busy} elapsed={elapsed} waking={health.data?.space==='waking'} error={error} category={current?categoryFor(current.result):undefined} onPhoto={upload} onDemo={demo} onRetry={()=>retryFile.current?analyzeFile(retryFile.current):demo()} onAdd={addCurrent} added={!!current&&items.some(i=>i.id===current.id)} onDrops={()=>setSheet({kind:'drops'})} onPreview={src=>setSheet({kind:'photo',src})}/>}/>
        <Route path="/laci" element={<Drawer catalog={catalog.data||[]} onAbout={()=>setSheet({kind:'about'})} onPhoto={upload} onDemo={demo} onReport={()=>setSheet({kind:'report'})}/>}/>
        <Route path="/katalog" element={<Catalog query={catalog} onAbout={()=>setSheet({kind:'about'})} onCategory={id=>setSheet({kind:'category',id})}/>}/>
        <Route path="*" element={<Empty title="Halaman tidak ditemukan"><p>Kembali ke beranda untuk mulai.</p><NavLink className="button primary" to="/">Ke beranda</NavLink></Empty>}/>
      </Routes></main>
      <nav className="bottom-nav" aria-label="Navigasi utama"><NavLink to="/" end className={({isActive})=>isActive||location.pathname==='/hasil'?'active':''}><span><House size={23}/></span>Beranda</NavLink><NavLink to="/laci"><span><FolderOpen size={23}/></span>Cek Laci{items.length>0&&<i>{items.length}</i>}</NavLink><NavLink to="/katalog"><span><Grid2X2 size={22}/></span>Katalog</NavLink></nav>
    </div>
    <input hidden ref={fileInput} type="file" accept="image/jpeg,image/png,image/webp" onChange={e=>{const f=e.target.files?.[0];e.target.value='';if(f)void analyzeFile(f)}}/>
    <input hidden ref={cameraInput} type="file" accept="image/*" capture="environment" onChange={e=>{const f=e.target.files?.[0];e.target.value='';if(f)void analyzeFile(f)}}/>
    {toast&&<div role="status" className="toast"><Check size={18}/>{toast}</div>}
    <SheetModal sheet={sheet} close={closeSheet}>
      {sheet?.kind==='about'&&<About/>}
      {sheet?.kind==='upload'&&<div className="upload-sheet"><span className="section-kicker">SATU FOTO, SATU BARANG</span><h2>Mulai dari mana?</h2><p>Letakkan satu barang di tempat terang. Pastikan seluruh barang terlihat di foto.</p><div className="upload-art"><img src="/illustrations/ponsel-retak.svg" alt="Ilustrasi ponsel retak" width="832" height="480"/></div><button className="button primary" onClick={()=>cameraInput.current?.click()}><Camera size={20}/>Ambil foto</button><button className="button secondary" onClick={()=>fileInput.current?.click()}><ImageIcon size={20}/>Pilih dari galeri</button><button className="text-button centered" onClick={demo}>Coba contoh terlebih dahulu <ArrowRight size={16}/></button><p className="fine-print">JPG, PNG, atau WEBP. Foto diperkecil sebelum dikirim ke layanan AI.</p></div>}
      {sheet?.kind==='category'&&<CategoryDetail id={sheet.id} onPhoto={()=>{setSheet(null);upload()}} onPreview={src=>setSheet({kind:'photo',src,categoryId:sheet.id})}/>}
      {sheet?.kind==='report'&&<Report catalog={catalog.data||[]} notify={notify}/>}
      {sheet?.kind==='drops'&&<DropPoints/>}
      {sheet?.kind==='photo'&&<div className="photo-preview-sheet"><h2>{sheet.categoryId!==undefined?'Foto referensi':'Foto barang'}</h2><div className="photo-preview-image"><img src={sheet.src} alt={sheet.categoryId!==undefined?'Foto referensi secara utuh':'Foto barang secara utuh'}/></div></div>}
    </SheetModal>
  </div>
}

function Home({onAbout,onPhoto,onCamera,onGallery,onDemo}:{onAbout:()=>void;onPhoto:()=>void;onCamera:()=>void;onGallery:()=>void;onDemo:()=>void}) {
  return <div className="home-page"><div className="home-header"><PageHeader onAbout={onAbout}/><span className="home-kicker">LANGKAH KECIL DARI RUMAH</span><h1>Barang lama di rumah?<br/>Kenal-E dulu.</h1><span className="header-ring"/></div><div className="home-body"><div className="hero-visual"><img className="hero-illustration" src="/illustrations/ponsel-retak.svg" alt="Ilustrasi ponsel retak dalam bingkai pemindai" width="832" height="480" fetchPriority="high"/></div><div className="home-copy"><h2>Kenali barangmu</h2><p>Foto satu barang untuk mulai memilah.</p></div><div className="home-actions"><button className="button primary" onClick={onCamera}><Camera size={21}/>Ambil foto</button><button className="text-button centered gallery-action" onClick={onGallery}><ImageIcon size={20}/>Pilih dari galeri</button></div><NavLink to="/laci" className="drawer-banner"><span className="banner-icon"><FolderOpen size={27}/></span><span><strong>Cek Laci</strong><small>Pilah barang yang menumpuk.</small></span><ChevronRight size={19}/></NavLink><button className="text-button centered demo-link" onClick={onDemo}>Mau lihat dulu? Coba contoh <ArrowRight size={15}/></button><button className="sr-only" onClick={onPhoto}>Pilih cara unggah foto</button></div></div>
}

function Result({current,busy,elapsed,waking,error,category,onPhoto,onDemo,onRetry,onAdd,added,onDrops,onPreview}:{current:Current|null;busy:boolean;elapsed:number;waking:boolean;error:ApiError|null;category?:Category;onPhoto:()=>void;onDemo:()=>void;onRetry:()=>void;onAdd:()=>void;added:boolean;onDrops:()=>void;onPreview:(src:string)=>void}) {
  const navigate=useNavigate(),r=current?.result
  return <div className="result-page"><header className="result-header"><button className="icon-button outlined" aria-label="Kembali ke beranda" onClick={()=>navigate('/')}><ArrowLeft size={20}/></button><span>Hasil identifikasi</span><button className="icon-button" onClick={onPhoto} aria-label="Foto barang lain"><Camera size={20}/></button></header>
    {busy?<div className="loading-state" role="status" aria-live="polite"><div className="scan-art"><DeviceArt device="phone"/><div className="scan-line"/></div><span className="loading-dot"><LoaderCircle className="spin" size={22}/></span><h2>{waking?'Layanan AI sedang bangun':'Sedang melihat barangmu'}</h2><p>{elapsed<15?'Mencari kemiripan dengan data referensi.':'Proses pertama bisa lebih lama. Tetap di halaman ini, ya.'}</p><span className="loading-steps">Mengenali bentuk <span/> Membandingkan detail</span></div>
    :error?<div className="result-empty"><Empty icon={<CloudOff/>} title="Foto belum bisa diproses"><p>{error.message}</p><button className="button primary" onClick={onRetry}>Coba lagi <ArrowRight size={18}/></button><button className="text-button centered" onClick={onPhoto}>Pilih foto lain</button><button className="text-button centered" onClick={onDemo}>Coba contoh</button></Empty></div>
    :!r?<Empty title="Belum ada foto"><p>Ambil atau unggah satu foto elektronik untuk melihat hasilnya.</p><button className="button primary" onClick={onPhoto}><Camera size={19}/>Pilih foto</button></Empty>
    :r.status==='out_of_reference'?<><ResultPhoto photo={current?.photo||null} alt="Foto barang yang belum dikenali" className="unknown-photo" onPreview={onPreview}><Search size={64}/></ResultPhoto><div className="unknown-copy"><span className="neutral-chip"><Search size={14}/>Belum dikenali</span><h1>Barang ini belum ada<br/>di data kami.</h1><p>Coba latar yang lebih sederhana dan pastikan hanya satu barang terlihat.</p><button className="button primary" onClick={onPhoto}><Camera size={19}/>Coba foto lain</button><button className="text-button centered" onClick={onAdd}>{added?'Buka Cek Laci':'Simpan untuk ditanyakan ke pengelola'}<ArrowRight size={16}/></button></div></>
    :<>{r.demo&&<div className="example-banner"><Info size={15}/>Contoh dari referensi, bukan analisis foto baru.</div>}<ResultPhoto photo={current?.photo||null} alt="Foto barang yang dianalisis" onPreview={onPreview}><DeviceArt device={category?.device||'pcb'} label="Ilustrasi papan sirkuit"/></ResultPhoto><div className="result-title"><h1>{r.macro?.name}</h1><div><p>{r.sub?`Mirip kelompok: ${r.sub.label}`:'Kelompok visual belum tersedia'}</p>{r.info&&<RiskBadge risk={r.info.risk_level}/>}</div></div>
      {!r.info?.assessable&&<p className="info-note">Campuran, perlu dipilah. Foto ulang setiap barang secara terpisah.</p>}
      <div className="result-details"><details><summary><Shield size={20}/>Cara menangani<ChevronDown size={18}/></summary>{r.info&&<Handling info={r.info}/>}</details><details><summary><ImageIcon size={20}/>Lihat 5 gambar mirip<ChevronDown size={18}/></summary><div className="similar-content">{r.similar.some(s=>s.url)?<div className="similar-grid">{r.similar.filter(s=>s.url).map((s,i)=><img key={i} loading="lazy" decoding="async" src={assetUrl(s.url!)} alt={'Referensi serupa '+(i+1)}/>)}</div>:<p>Gambar referensi belum tersedia untuk ditampilkan. Hasil ini masih perlu diperiksa.</p>}</div></details></div>
      <PriceView price={r.price} info={r.info}/><button className="button primary" onClick={onAdd}>{added?<Check size={20}/>:<Plus size={20}/>} {added?'Buka Cek Laci':'Tambah ke Cek Laci'}</button><button className="text-button centered drop-action" onClick={onDrops}><MapPin size={18}/>Cari tempat setor</button></>}
  </div>
}


function ResultPhoto({photo,alt,className='',onPreview,children}:{photo:string|null;alt:string;className?:string;onPreview:(src:string)=>void;children:ReactNode}) {
  return <div className={'result-photo '+className}>{photo?<><img src={photo} alt={alt}/><button className="photo-expand-button" aria-label="Lihat foto penuh" aria-haspopup="dialog" title="Lihat foto penuh" onClick={()=>onPreview(photo)}><Maximize2 size={18}/></button></>:children}</div>
}

function Handling({info}:{info:InfoData}) {return <div className="handling">{!info.verified&&<span className="draft-label">Draf, belum diverifikasi</span>}{info.hazard_note&&<p>{info.hazard_note}</p>}{info.assessable&&info.risk_level!=='unknown'?<>{info.do.length>0&&<div><h4>Lakukan</h4>{info.do.map(t=><p className="handling-row" key={t}><Check size={15}/>{t}</p>)}</div>}{info.dont.length>0&&<div><h4>Hindari</h4>{info.dont.map(t=><p className="handling-row" key={t}><X size={15}/>{t}</p>)}</div>}</>:<p>{info.assessable?'Klasifikasi risiko belum tersedia. Tanyakan kepada pengelola.':'Campuran, perlu dipilah. Panduan khusus belum tersedia.'}</p>}</div>}

function PriceView({price,info}:{price:Price|null;info:InfoData|null}) {
  const [weight,setWeight]=useState('1')
  if(price?.mode==='ranges')return <div className="price-estimates"><span className="section-kicker">ACUAN HARGA · HASIL RISET WEB</span>{price.whole&&<PriceEstimateView label="Jual utuh, jika masih berfungsi" quote={price.whole}/>}{price.scrap&&<PriceEstimateView label="Jual rongsok" quote={price.scrap}/>}<p className="fine-print">Harga penawaran/acuan pengepul, belum dikonfirmasi untuk Semarang. Fungsi barang tidak ditentukan dari foto.</p></div>
  if(!price||price.mode==='none'||!price.verified)return <div className="price-unavailable"><Tag size={17}/><span>Nilai rongsok <span>·</span> Belum ada estimasi</span></div>
  if(price.mode==='no_value')return <p className="info-note">Umumnya tidak bernilai jual; fokus ke penanganan.</p>
  const numberWeight=Number(weight),factor=price.mode==='per_kg'?numberWeight:1,valid=Number.isFinite(factor)&&factor>0
  return <div className="price-block"><span className="section-kicker">PERKIRAAN KASAR · RONGSOK</span>{price.mode==='per_kg'&&<><label htmlFor="weight">Berat barang (kg)</label><input id="weight" type="number" min="0.001" step="0.1" value={weight} onChange={e=>setWeight(e.target.value)}/><div className="weight-choices">{[.1,1,5].map(w=><button key={w} onClick={()=>setWeight(String(w))}>{w===.1?'±1 ons':`±${w} kg`}</button>)}</div></>}{valid?<strong>{rupiah((price.min||0)*factor)}–{rupiah((price.max||0)*factor)}</strong>:<p>Masukkan berat lebih dari nol.</p>}<small>Sumber: {price.source} · {price.source_date}</small><p className="fine-print">Jangan membongkar barang demi menjual per bagian.{info?.hazard_note.includes('data')?' Hapus data pribadi sebelum menjual.':''}</p></div>
}

function PriceEstimateView({label,quote}:{label:string;quote:PriceEstimate}) {
  return <div className="price-estimate"><h4>{label}</h4><strong>{rupiah(quote.min)}{quote.max!==quote.min&&<>–{rupiah(quote.max)}</>} <small>/ {quote.unit==='kg'?'kg':'barang'}</small></strong>{quote.requires_confirmation.includes('pcb_grade')&&<p className="price-grade-note">Grade PCB perlu dikonfirmasi pengepul.</p>}<details className="price-method"><summary>Dasar estimasi</summary><p>{quote.note}</p></details><span className="price-sources">{quote.sources.map(source=><a key={source.url} href={source.url} target="_blank" rel="noopener noreferrer">{source.title}</a>)}<span>Diakses {quote.accessed_on}</span></span></div>
}

function ItemRow({item,categories}:{item:SavedItem;categories:Category[]}) {const cat=categories.find(c=>c.id===item.result.macro?.id);return <div className="item-row"><span className="item-thumb">{item.photo?<img src={item.photo} alt=""/>:<DeviceArt device={cat?.device||'mixed'}/>}</span><span className="item-description"><strong>{item.result.macro?.name||'Barang belum dikenali'}</strong><RiskBadge risk={itemRisk(item)}/>{item.result.demo&&<small className="example-marker">Contoh</small>}{item.result.corrected&&<small className="example-marker">Dikoreksi manual</small>}</span></div>}

function Drawer({catalog,onAbout,onPhoto,onDemo,onReport}:{catalog:Category[];onAbout:()=>void;onPhoto:()=>void;onDemo:()=>void;onReport:()=>void}) {
  const {items,hydrated}=useDrawer(),[showAll,setShowAll]=useState(false)
  const counts=summarize(items),priority=items.filter(i=>itemRisk(i)==='high'),others=items.filter(i=>itemRisk(i)!=='high')
  return <div className="standard-page drawer-page"><PageHeader onAbout={onAbout}/><div className="page-title"><span className="section-kicker">SATU PER SATU, LEBIH TERARAH</span><h1>Cek Laci</h1><p>{items.length?`${items.length} barang tersimpan di perangkat.`:'Beri langkah baru untuk isi lacimu.'}</p></div>{!hydrated?<div className="loading-inline"><LoaderCircle className="spin"/>Memuat barangmu…</div>:!items.length?<Empty icon={<img src="/illustrations/folder-krem-sage.svg" alt="" width="512" height="512"/>} title="Lacimu masih kosong"><p>Tambahkan elektronik yang sudah tak terpakai. Kita mulai dari satu barang dulu.</p><button className="button primary" onClick={onPhoto}><Plus size={20}/>Tambah barang pertama</button><button className="text-button centered" onClick={onDemo}>Coba dengan barang contoh <ArrowRight size={16}/></button></Empty>:<><button className="summary-card" onClick={onReport}><span className="summary-icon"><Shield size={25}/></span><span><strong>{counts.high?'Mulai dari yang berisiko':'Barangmu sudah terkumpul'}</strong><small>{counts.high?`${counts.high} barang perlu diprioritaskan.`:'Lihat pembagian barang menurut risiko.'}</small><span className="summary-link">Lihat rapor pemilahan <ChevronRight size={16}/></span></span></button>{priority.length>0&&<section className="drawer-section"><h2>Setor dulu <CircleAlert size={20}/></h2>{priority.map(i=><ItemRow key={i.id} item={i} categories={catalog}/>)}</section>}{others.length>0&&<section className="drawer-section"><h2>{priority.length?'Barang lainnya':'Barang di lacimu'}</h2>{(showAll?others:others.slice(0,2)).map(i=><ItemRow key={i.id} item={i} categories={catalog}/>)}{others.length>2&&<button className="text-button centered" onClick={()=>setShowAll(!showAll)}>{showAll?'Tampilkan lebih sedikit':`Lihat ${others.length-2} barang lainnya`}<ChevronDown size={16}/></button>}</section>}<div className="drawer-actions"><button className="text-button centered" onClick={onPhoto}><Plus size={20}/>Tambah barang</button><button className="button primary" onClick={onReport}><ArrowDownToLine size={19}/>Simpan rapor</button><p className="fine-print">Tersimpan di perangkat ini. Kamu bisa lanjut nanti.</p></div></>}</div>
}

function Catalog({query,onAbout,onCategory}:{query:ReturnType<typeof useQuery<Category[],Error>>;onAbout:()=>void;onCategory:(id:number)=>void}) {
  const [search,setSearch]=useState(''),[filters,setFilters]=useState(emptyFilters)
  const all=query.data||[],filtered=all.filter(c=>matchesCatalog(c,filters,search))
  const sorted=[4,13,9,...all.map(c=>c.id).filter(id=>![4,13,9].includes(id))].map(id=>filtered.find(c=>c.id===id)).filter((c):c is Category=>!!c)
  return <div className="standard-page catalog-page"><PageHeader onAbout={onAbout}/><div className="page-title"><h1>Kenali e-waste<br/>di rumahmu</h1><p>Jelajahi kategori barang.</p></div><label className="search-field"><Search size={20}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Cari barang" aria-label="Cari kategori barang"/>{search&&<button onClick={()=>setSearch('')} aria-label="Hapus pencarian"><X size={16}/></button>}</label><CatalogFilters value={filters} onChange={setFilters} count={query.data?sorted.length:undefined}/>{query.isPending?<div className="loading-inline"><LoaderCircle className="spin"/>Memuat katalog…</div>:query.error?<ErrorPanel message="Katalog belum bisa dimuat. Pastikan backend sedang berjalan." onRetry={()=>void query.refetch()}/>:sorted.length===0?<Empty icon={<Search/>} title="Belum ketemu"><p>Coba kata kunci lain atau ubah filter barang.</p><button className="text-button centered" onClick={()=>{setSearch('');setFilters(emptyFilters())}}>Tampilkan semua kategori</button></Empty>:<div className="catalog-list">{sorted.map(c=><button className="catalog-row" key={c.id} onClick={()=>onCategory(c.id)}><span className="catalog-thumb">{c.thumb_url?<img loading="lazy" decoding="async" src={assetUrl(c.thumb_url)} alt=""/>:<DeviceArt device={c.device}/>}</span><span><strong>{c.name}</strong><CategoryLabels category={c}/><CategoryRisks category={c}/></span><ChevronRight size={19}/></button>)}</div>}<p className="catalog-note"><Info size={15}/>Pilih barang untuk melihat panduan.</p></div>
}

function SheetModal({sheet,close,children}:{sheet:Sheet;close:()=>void;children:ReactNode}) {
  const dialog=useRef<HTMLDialogElement>(null),previousFocus=useRef<HTMLElement|null>(null)
  useEffect(()=>{const d=dialog.current;if(!d)return;if(sheet){previousFocus.current=document.activeElement as HTMLElement;d.showModal()}else if(d.open)d.close();return()=>{if(d.open)d.close()}},[!!sheet])
  useLayoutEffect(()=>{if(sheet){dialog.current?.scrollTo(0,0);if(sheet.kind==='photo')dialog.current?.querySelector<HTMLButtonElement>('.sheet-close')?.focus({preventScroll:true})}},[sheet?.kind])
  const isMap=sheet?.kind==='drops',isPhoto=sheet?.kind==='photo',isFramed=isMap||isPhoto||sheet?.kind==='upload'||sheet?.kind==='category'
  useLayoutEffect(()=>{
    if(!isFramed)return
    const frame=document.querySelector<HTMLElement>('.phone-app'),d=dialog.current
    if(!frame||!d)return
    const position=()=>{
      const bounds=frame.getBoundingClientRect()
      const top=Math.max(0,bounds.top+frame.clientTop),bottom=Math.min(window.innerHeight,bounds.bottom-frame.clientTop)
      d.style.setProperty('--frame-left',`${bounds.left+frame.clientLeft}px`)
      d.style.setProperty('--frame-top',`${top}px`)
      d.style.setProperty('--frame-width',`${bounds.width-2*frame.clientLeft}px`)
      d.style.setProperty('--frame-height',`${Math.max(0,bottom-top)}px`)
    }
    window.scrollTo(0,0)
    position()
    const observer=new ResizeObserver(position)
    observer.observe(frame)
    window.addEventListener('resize',position)
    window.addEventListener('scroll',position,true)
    const previousOverflow=document.body.style.overflow
    document.body.style.overflow='hidden'
    return()=>{observer.disconnect();window.removeEventListener('resize',position);window.removeEventListener('scroll',position,true);document.body.style.overflow=previousOverflow}
  },[isFramed])
  return <dialog className={'sheet-modal'+(isFramed?' frame-modal':'')+(isMap?' map-modal':'')+(isPhoto?' photo-modal':'')} ref={dialog} aria-label={isPhoto?'Foto lengkap':sheet?.kind==='report'?'Rapor Cek Laci':sheet?.kind==='drops'?'Cari tempat setor':sheet?.kind==='category'?'Detail kategori':sheet?.kind==='about'?'Tentang Kenal-E':'Pilih foto'} onCancel={e=>{e.preventDefault();close()}} onClose={()=>{previousFocus.current?.focus();close()}} onClick={e=>{if(e.target===e.currentTarget)close()}}><div className="sheet-inner"><div className="sheet-handle"/><button className="icon-button sheet-close" aria-label="Tutup panel" onClick={close}><X size={21}/></button>{children}</div></dialog>
}

function CategoryDetail({id,onPhoto,onPreview}:{id:number;onPhoto:()=>void;onPreview:(src:string)=>void}) {
  const query=useQuery({queryKey:['category',id],queryFn:()=>api.category(id)})
  const c=query.data
  if(query.isPending)return <div className="loading-inline"><LoaderCircle className="spin"/>Memuat kategori…</div>
  if(!c)return <ErrorPanel message="Detail belum bisa dimuat." onRetry={()=>void query.refetch()}/>
  return <div className="category-detail"><ResultPhoto photo={c.thumb_url?assetUrl(c.thumb_url):null} alt={c.name} className="detail-art" onPreview={onPreview}><DeviceArt device={c.device} label={'Ilustrasi '+c.name}/></ResultPhoto><span className="section-kicker">KATALOG KENAL-E</span><h2>{c.name}</h2>{c.description&&<p className="category-description">{c.description}</p>}<CategoryLabels category={c}/><CategoryRisks category={c}/><p className="category-count">{c.size} citra referensi · {c.n_sub} kelompok visual</p>{!c.thumb_url&&<p className="fine-print">Ilustrasi kategori. Foto dataset belum tersedia untuk ditampilkan.</p>}<h3>Penanganan awal</h3>{c.info&&<Handling info={c.info}/>}<PriceView price={c.price||null} info={c.info||null}/>{c.subs&&c.subs.length>0&&<details className="sub-details"><summary>Kelompok visual <ChevronDown size={16}/></summary>{c.subs.map(s=><article className="subcluster-card" key={s.id}><strong>{s.name||`Kelompok visual ${s.id}`}</strong><small>{s.size} citra referensi</small>{s.description&&<p>{s.description}</p>}<div>{s.rep_urls.map(url=><img key={url} loading="lazy" decoding="async" src={assetUrl(url)} alt={'Referensi kelompok '+s.id}/>)}</div></article>)}</details>}<button className="button primary" onClick={onPhoto}><Camera size={19}/>Foto barang seperti ini</button></div>
}

function Report({catalog,notify}:{catalog:Category[];notify:(text:string)=>void}) {
  const items=useDrawer(s=>s.items),clear=useDrawer(s=>s.clear),counts=summarize(items),ref=useRef<HTMLDivElement>(null)
  const [exporting,setExporting]=useState(false),[confirm,setConfirm]=useState(false),[downloadUrl,setDownloadUrl]=useState(''),[exportError,setExportError]=useState(false),[attempt,setAttempt]=useState(0)
  useEffect(()=>{
    let cancelled=false,url=''
    setDownloadUrl('');setExportError(false)
    if(!items.length)return
    setExporting(true)
    void (async()=>{
      try{
        await document.fonts.ready
        if(cancelled||!ref.current)return
        const blob=await toBlob(ref.current,{pixelRatio:2,backgroundColor:'#fafbf8',cacheBust:false})
        if(!blob)throw new Error('PNG belum tersedia')
        if(!cancelled){url=URL.createObjectURL(blob);setDownloadUrl(url)}
      }catch{if(!cancelled)setExportError(true)}finally{if(!cancelled)setExporting(false)}
    })()
    return()=>{cancelled=true;if(url)URL.revokeObjectURL(url)}
  },[items,catalog,attempt])
  return <div className="report-sheet"><div className="report-capture" ref={ref}><Brand/><span className="section-kicker">RAPOR PEMILAHAN</span><h2>Isi lacimu,<br/>langkah berikutnya.</h2><p>{items.length} barang · {new Date().toLocaleDateString('id-ID',{day:'numeric',month:'long',year:'numeric'})}</p>{items.some(i=>i.result.demo)&&<div className="example-banner">Termasuk {items.filter(i=>i.result.demo).length} barang contoh.</div>}<div className="report-counts">{riskOrder.map(r=><div key={r} className={r}><strong>{counts[r]}</strong><span>{riskLabels[r]}</span></div>)}{counts.unrecognized>0&&<div className="unrecognized"><strong>{counts.unrecognized}</strong><span>Belum dikenali</span></div>}</div>{counts.high>0&&<div className="report-priority"><CircleAlert size={19}/><span>Setor dulu: {items.filter(i=>itemRisk(i)==='high').map(i=>i.result.macro?.name).join(', ')}.</span></div>}{[...riskOrder,'unrecognized' as const].filter(r=>counts[r]>0).map(r=><section className="report-group" key={r}><h3><RiskBadge risk={r}/><span>{counts[r]} barang</span></h3>{r!=='unrecognized'&&<p>{riskDescriptions[r]}</p>}{items.filter(i=>itemRisk(i)===r).map(i=><div key={i.id} className="report-item"><span className="report-device"><DeviceArt device={catalog.find(c=>c.id===i.result.macro?.id)?.device||'mixed'}/></span><span>{i.result.macro?.name||'Barang belum dikenali'}{i.result.demo&&<small>Contoh dari referensi</small>}</span></div>)}</section>)}<div className="report-footer"><p>Pembagian ini adalah panduan pemilahan awal. Keterangan risiko masih draf, belum diverifikasi. Jangan mencampur barang berisiko dalam satu wadah.</p><span>Kenal-E · Kemiripan visual, bukan diagnosis.</span></div></div>{downloadUrl?<a className="button primary" href={downloadUrl} download={'rapor-kenal-e-'+new Date().toISOString().slice(0,10)+'.png'}><ArrowDownToLine size={19}/>Unduh rapor PNG</a>:<button className="button primary" disabled={exporting||!items.length} onClick={()=>setAttempt(n=>n+1)}>{exporting?<LoaderCircle className="spin" size={19}/>:<ArrowDownToLine size={19}/>} {exporting?'Menyiapkan gambar…':exportError?'Coba siapkan PNG lagi':'Siapkan rapor PNG'}</button>}{exportError&&<p className="fine-print">Gambar belum bisa dibuat. Coba siapkan lagi.</p>}{confirm?<div className="confirm-clear"><p>Kosongkan semua barang? Setelah dihapus, daftar ini tidak bisa dikembalikan.</p><button className="button danger-button" onClick={()=>{clear();setConfirm(false);notify('Cek Laci dikosongkan')}}>Ya, kosongkan</button><button className="text-button centered" onClick={()=>setConfirm(false)}>Batal</button></div>:<button className="text-button centered danger" disabled={!items.length} onClick={()=>setConfirm(true)}><Trash2 size={17}/>Kosongkan Cek Laci</button>}</div>
}


function About(){return <div className="about-sheet"><Brand/><span className="section-kicker">DARI RUMAH, SATU LANGKAH DULU</span><h2>Kenali. Pilah. Setor.</h2><p>Kenal-E membantu mengenali elektronik lama dan merencanakan pemilahan awal, mulai dari foto satu barang.</p><div className="about-points"><div><Search size={21}/><span><strong>Berdasarkan kemiripan visual</strong><p>Hasil bukan diagnosis dan tidak menilai apakah barang masih berfungsi. Kandidat masih perlu diperiksa.</p></span></div><div><Shield size={21}/><span><strong>Panduan masih berupa draf</strong><p>Catatan risiko dan penanganan memerlukan verifikasi. Jangan membongkar barang untuk memeriksa hasil.</p></span></div><div><Tag size={21}/><span><strong>Harga perlu sumber</strong><p>Angka hanya ditampilkan jika rentang harga, sumber, dan tanggal telah diverifikasi.</p></span></div><div><FolderOpen size={21}/><span><strong>Cek Laci tersimpan di perangkat</strong><p>Daftar serta salinan foto tersimpan di browser ini. Hapus barang atau kosongkan Cek Laci untuk menghapusnya.</p></span></div><div><Camera size={21}/><span><strong>Foto diproses di layanan AI</strong><p>Backend menghapus file sementara setelah permintaan selesai. Layanan HF Space dapat menyimpan unggahan sementara hingga pembersihan cache.</p></span></div></div></div>}
