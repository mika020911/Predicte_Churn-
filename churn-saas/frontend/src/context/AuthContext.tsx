'use client';

import React, {createContext, useContext, useEffect, useState} from "react";
import { useRouter } from "next/navigation";
import {User, LoginPayload, RegisterPayload} from '@/types/auth'
import { loginApi, registerAPI, getMeApi } from "@/lib/api/auth";

interface AuthContextType{
    user: User | null;
    token: string | null;
    loading: Boolean;
    login: (payload:LoginPayload) => Promise<void>;
    register: (payload:RegisterPayload) => Promise<void>;
    logout: () => void;
}

const AuthContext =createContext<AuthContextType | undefined>(undefined)

export function AuthProvider ({children}: {children: React.ReactNode}) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string |null>(null);
    const [loading, setLoading] = useState<Boolean>(true);
    const router = useRouter();

    useEffect(()=> {
        const stroredToken = localStorage.getItem('churnsight_token');
        if (stroredToken){
            setToken(stroredToken);
            getMeApi(stroredToken)
            .then((userData)=>  setUser(userData))
            .catch(()=>{
                localStorage.removeItem('churnsight_token');
                setToken(null);
                setUser(null);
            })
            .finally(()=> setLoading(false)); 
        } else{
            setLoading(false);
        }
    },[]);

    const login = async (payload: LoginPayload)=>{
        const data = await loginApi(payload);
        localStorage.setItem('churnsight_token', data.access_token);
        setToken(data.access_token);
        const userData = await getMeApi(data.access_token);
        setUser(userData);
        router.push('/dashboard');
    };
    
    const register = async(payload: RegisterPayload)=>{
        await registerAPI(payload);
        
        router.push('/auth/login?success=account_created');
//auto
        //await login ({email: payload.email, password:payload.password});

    };

    const logout = ()=>{
        localStorage.removeItem('churnsight_token');
        setToken(null);
        setUser(null);
        router.push('/auth/login');

    };

    return(
        <AuthContext.Provider value={{user, token, loading, login, register, logout}}>
            {children}
        </AuthContext.Provider>
    );
}
export function useAuth(){
    const context = useContext(AuthContext);
    if (!context){
        throw new Error("useAuth doit être utilisé au sein d'un AuthProvider")

    }
    return context;
}