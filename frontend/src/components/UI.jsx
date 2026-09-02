import React from 'react';
import{formatCurrency,DEFAULT_CURRENCY}from'../utils/currency';

export const icons={overview:'⌂',accounts:'▣',transactions:'⇄',budgets:'◔',reports:'◫',categories:'◇',recurring:'↻',goals:'◎',security:'♢',activity:'◷',profile:'◉',settings:'⚙',notifications:'♧',search:'⌕',plus:'+'};
export function Icon({name}){return <span className="icon" aria-hidden="true">{icons[name]||name}</span>}
export function Button({children,variant='primary',className='',...props}){return <button className={`btn ${variant} ${className}`} {...props}>{children}</button>}
export function Card({children,className='',...props}){return <section className={`card ${className}`} {...props}>{children}</section>}
export function Badge({children,tone='neutral'}){return <span className={`badge ${tone}`}>{children}</span>}
export function Empty({title='Nothing here yet',text='Create your first item to start keeping track of your money.',action}){return <div className="empty"><div className="empty-mark">◌</div><strong>{title}</strong><p>{text}</p>{action}</div>}
export function Loading({lines=3}){return <div className="loading">{Array.from({length:lines},(_,i)=><i key={i}/>)}</div>}
export function Modal({title,children,onClose}){return <div className="modal" role="dialog" aria-modal="true"><div className="modal-box"><div className="modal-title"><h2>{title}</h2><button aria-label="Close" className="icon-btn" onClick={onClose}>×</button></div>{children}</div></div>}
export function Avatar({user,size=''}){const name=user?.name||[user?.first_name,user?.last_name].filter(Boolean).join(' ')||user?.email||'U';return <span className={`avatar ${size}`} title={name}>{user?.avatar?<img src={user.avatar} alt=""/>:name.slice(0,2).toUpperCase()}</span>}
export const money=(value,currency=DEFAULT_CURRENCY,options)=>formatCurrency(value,currency,options);
export function PageHeader({eyebrow,title,children}){return <header className="page-header"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1></div><div className="header-actions">{children}</div></header>}
