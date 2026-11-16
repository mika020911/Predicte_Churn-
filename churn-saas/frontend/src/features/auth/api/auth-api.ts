import type {
  LoginPayload,
  RegisterPayload,
  TokenResponse,
  User,
} from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

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
            
        },
    });
    if (!response.ok){
        throw new Error('Session expirée ou invalide')
    }
    return response.json();
    
}

export async function requestPasswordReset(email: string): Promise<string> {
  const response = await fetch(`${API_URL}/auth/forgot-password`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email }),
  });

  const body = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : "Impossible de demander la réinitialisation.",
    );
  }

  return body.message;
}

export async function submitNewPassword(
  token: string,
  newPassword: string,
): Promise<string> {
  const response = await fetch(`${API_URL}/auth/reset-password`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      token,
      new_password: newPassword,
    }),
  });

  const body = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : "Le lien est invalide ou expiré.",
    );
  }

  return body.message;
}