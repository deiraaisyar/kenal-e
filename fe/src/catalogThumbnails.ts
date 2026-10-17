// Fixed, bundled catalog artwork. Full-size reference images remain separate.
const thumbnails=import.meta.glob<string>('./assets/catalog/*.webp',{
  eager:true,
  query:'?url',
  import:'default',
})
export const catalogThumbnail=(id:number):string|undefined=>thumbnails[`./assets/catalog/${id}.webp`]
