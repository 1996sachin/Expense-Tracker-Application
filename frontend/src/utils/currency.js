export const DEFAULT_CURRENCY='NPR';
export const CURRENCY_OPTIONS=[
  {code:'NPR',label:'NPR — Nepalese Rupee'},
  {code:'USD',label:'USD — US Dollar'},
  {code:'EUR',label:'EUR — Euro'},
  {code:'GBP',label:'GBP — British Pound'},
];

export function formatCurrency(amount,currency=DEFAULT_CURRENCY,{compact=false}={}){
  const value=Number(amount||0);
  const options={style:'currency',currency,minimumFractionDigits:compact?0:2,maximumFractionDigits:compact?1:2,...(compact?{notation:'compact',compactDisplay:'short'}:{})};
  const formatted=new Intl.NumberFormat('en-NP',options).formatToParts(value);
  return formatted.map(part=>part.type==='currency'&&currency==='NPR'?'Rs.':part.value).join('').replace(/Rs\.\s*/, 'Rs. ');
}
