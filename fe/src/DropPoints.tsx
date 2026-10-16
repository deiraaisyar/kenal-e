import {LocateFixed,MapPin,Navigation} from 'lucide-react'

const buildings = [
  [24,36,48,28],[90,24,32,47],[150,29,59,30],[237,19,35,45],[303,27,55,26],[382,17,34,49],
  [18,100,37,50],[79,94,57,27],[160,92,40,45],[253,93,42,25],[327,88,32,48],[384,100,42,31],
  [25,185,49,27],[97,158,30,45],[160,177,51,30],[279,165,44,30],[352,164,63,26],
  [18,269,45,35],[87,240,35,37],[153,255,39,49],[281,256,33,41],[348,241,47,35],
  [23,350,34,44],[80,329,52,25],[152,362,38,29],[280,350,50,28],[355,326,62,30],
  [17,433,45,30],[94,415,33,50],[164,448,42,32],[271,430,51,32],[358,422,36,44],
  [30,511,43,30],[101,503,55,34],[181,527,34,33],[278,506,37,48],[359,518,59,28],
]

function DemoMap() {
  return <svg className="drop-map-art" viewBox="0 0 440 570" preserveAspectRatio="xMidYMid slice" role="img" aria-labelledby="drop-map-title drop-map-description">
    <title id="drop-map-title">Peta ilustrasi area UNDIP, Tembalang, Semarang</title>
    <desc id="drop-map-description">Lima pin hijau merupakan contoh tempat setor. Titik lokasi dan susunan jalan hanya untuk demo, bukan lokasi nyata.</desc>
    <defs>
      <pattern id="map-grain" width="10" height="10" patternUnits="userSpaceOnUse"><circle cx="3" cy="3" r=".5" fill="#bec8bb" opacity=".25"/></pattern>
    </defs>
    <rect width="440" height="570" fill="#e9ece5"/>
    <path d="M207 85 307 117 336 230 261 294 177 249 165 147Z" fill="#dce7d3"/>
    <path d="M-12 407 64 391 85 469 47 514-12 500Z M329 479 388 470 452 500 451 579 331 579Z" fill="#dce7d3"/>
    <g fill="#dce1d8" stroke="#d0d7cc" strokeWidth="1.2">{buildings.map(([x,y,w,h],i)=><rect key={i} x={x} y={y} width={w} height={h} rx="3" transform={`rotate(${i%3===0?-9:4} ${x+w/2} ${y+h/2})`}/>)}</g>
    <g fill="none" strokeLinecap="round" strokeLinejoin="round">
      <g stroke="#d3d9ce" strokeWidth="21"><path d="M-20 160 114 145 221 155 335 138 465 151"/><path d="M66-20 73 103 141 213 137 376 168 590"/><path d="M-20 323 117 310 246 323 451 292"/><path d="M302-20 273 92 243 197 236 349 255 590"/></g>
      <g stroke="#fffefa" strokeWidth="15"><path d="M-20 160 114 145 221 155 335 138 465 151"/><path d="M66-20 73 103 141 213 137 376 168 590"/><path d="M-20 323 117 310 246 323 451 292"/><path d="M302-20 273 92 243 197 236 349 255 590"/></g>
      <g stroke="#f8f9f4" strokeWidth="8"><path d="M-10 76 164 70 257 74 453 61"/><path d="M-10 227 105 215 207 235 338 215 460 220"/><path d="M-10 402 112 390 234 405 456 379"/><path d="M-10 488 133 482 245 491 453 478"/><path d="M215-10 218 76 203 145"/><path d="M360 69 345 144 331 221 327 309 338 392 322 486 334 590"/></g>
      <path d="M-15 553C86 534 118 559 192 548S299 548 458 522" stroke="#d0ded9" strokeWidth="9"/>
    </g>
    <rect width="440" height="570" fill="url(#map-grain)"/>

  </svg>
}

// Keep labels and markers outside the background SVG so resizing never stretches them.
function MapMarkers() {
  return <div className="map-markers" aria-hidden="true">
    <div className="map-campus-label"><span>AREA KAMPUS</span><strong>UNDIP</strong></div>
    <div className="map-district-label"><strong>Tembalang</strong><span>SEMARANG</span></div>
    <div className="map-user-position"><span className="map-user-radius"/><span className="map-user-dot"/><span className="map-user-label">Lokasi Anda</span></div>
    {[[20,43],[77,43],[84,65],[21,75],[62,84]].map(([left,top],i)=><span key={i} className="map-collection-pin" style={{left:`${left}%`,top:`${top}%`}}>
      <svg width="38" height="48" viewBox="0 0 38 48" fill="none">
        <path d="M19 45C15 39 3 29 3 18a16 16 0 1 1 32 0c0 11-12 21-16 27Z" fill="#367348" stroke="#fffefa" strokeWidth="3"/>
        <g stroke="#fff" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d="M13 14h12l-1 10H14Z M12 11h14 M17 8h4 M17 16v5 M21 16v5"/></g>
      </svg>
    </span>)}
  </div>
}

export default function DropPoints() {
  return <div className="drops-map-sheet">
    <div className="drop-map-canvas">
      <DemoMap/>
      <MapMarkers/>
      <div className="drop-map-heading"><span className="section-kicker">LANGKAH BERIKUTNYA</span><h2>Cari tempat setor</h2><span className="map-demo-badge">Demo</span></div>
      <div className="map-location-caption"><LocateFixed size={15}/><span>Area UNDIP, Tembalang</span></div>
      <div className="map-legend"><span/>Titik contoh</div>
    </div>
    <div className="drop-map-panel">
      <div className="drop-map-area"><span className="drop-map-area-icon"><MapPin size={23}/></span><div><h3>Di sekitar Tembalang</h3><p>Semarang, Jawa Tengah</p></div></div>
      <p className="drop-map-note">Peta dan titik masih ilustrasi. Lokasi setor terverifikasi segera menyusul.</p>
      <button className="button primary" disabled><Navigation size={17}/>Petunjuk arah segera tersedia</button>
    </div>
  </div>
}
