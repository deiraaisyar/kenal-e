export type Risk = 'high' | 'medium' | 'valuable' | 'low' | 'unknown'
export type Info = {weee:string; risk_level:Risk; bag:string; hazard_note:string; do:string[]; dont:string[]; assessable:boolean; verified:boolean}
export type Price = {mode:'none'|'no_value'|'per_kg'|'per_item'; min?:number; max?:number; source?:string; source_date?:string; verified?:boolean; weight_input?:boolean}
export type Category = {id:number;name:string;size:number;risk_level:Risk;bag:string;device:string;thumb_url:string|null;n_sub:number;info?:Info;price?:Price;subs?:{id:number;size:number;rep_urls:string[]}[]}
export type Analysis = {status:'in_reference'|'borderline'|'out_of_reference';macro:{id:number;name:string}|null;sub:{id:number;label:string}|null;info:Info|null;price:Price|null;similar:{url:string|null;macro:number;sub:number;sim:number}[];taxonomy_version:string;disclaimer:string;demo?:boolean;demo_note?:string;corrected?:boolean}
export type SavedItem = {id:string;photo:string|null;result:Analysis;createdAt:string}
export type DropPoint = {id:string;name:string;city:string;address:string;maps_url?:string;contact?:string;accepts:Risk[];verified_on:string}
