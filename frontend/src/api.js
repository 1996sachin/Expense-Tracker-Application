import axios from 'axios';
const api=axios.create({baseURL:import.meta.env.VITE_API_URL||'http://localhost:8000/api/'});
api.interceptors.request.use(c=>{const t=localStorage.getItem('access');if(t)c.headers.Authorization=`Bearer ${t}`;return c});
api.interceptors.response.use(r=>r,async e=>{const req=e.config;if(e.response?.status===401&&!req._retry&&localStorage.getItem('refresh')){req._retry=true;try{const {data}=await axios.post(`${api.defaults.baseURL}auth/refresh/`,{refresh:localStorage.getItem('refresh')});localStorage.setItem('access',data.access);req.headers.Authorization=`Bearer ${data.access}`;return api(req)}catch{localStorage.clear()}}return Promise.reject(e)});
export default api;
