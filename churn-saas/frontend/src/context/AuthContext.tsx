'use client';

import React, {createContext, useContext, useEffect, useState} from "react";
import { useRouter } from "next/navigation";
import {User, LoginPayload, RegisterPayload} from '@/types/auth'
import { loginApi, registerAPI, getMeApi } from "@/lib/api/auth";

interface AuthContextType{
    user: User | null;
    token: string | null;
    loading: boolean;
    login: (payload:LoginPayload) => Promise<void>;
    register: (payload:RegisterPayload) => Promise<void>;
    logout: () => void;
}

const AuthContext =createContext