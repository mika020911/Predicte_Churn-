import { LoginPayload, RegisterPayload, TokenResponse, User } from "@/types/auth";

const API_URL = process.env.NEXT_PUBLIC_URL || 'http://localhost:8000/api/v1';

export async function registerAPI(payload:RegisterPayload): Promise <User>{
    const response = await fetch (`${API_URL}/auth/register`, {
        method:'POST',
        headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
});
    if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Échec lors de la création du compte');
    }

    return response.json();
}

export async function loginApi (payload:LoginPayload): Promise<TokenResponse> {
    const response = await fetch (`${API_URL}/auth/login/json`, {
        method:'POST',
        headers:{'Content-Type': 'application/json'},
        body:JSON.stringify(payload)
    });
    if (!response.ok){
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Email ou mot de passe incorrect');
    }
    return response.json();
}

export async function getMeApi(token:string): Promise<User> {
    const response = await fetch (`${API_URL}/auth/me`, {
        method:'GET',
        headers:{
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application.json',
        },
    });
    if (!response.ok){
        throw new Error('Session expirée ou invalide')
    }
    return response.json();
    
}