export interface User{
    id:number;
    organization_id:number;
    email:string;
    full_name:string;
    role:string;
    is_active:boolean;
    created_at:string;
    update_at:string;
}

export interface TokenResponse{
    access_token: string;
    token_type: string;
}
export interface RegisterPayload {
    email: string;
    password: string;
    full_name: string;
    organization_name: string;
}

export interface LoginPayload {
    email: string;
    password: string;
}