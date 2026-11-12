import type {
    CustomerListParams,
    CustomerListResponse,
}from "../types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export async function getCustomers(
    token:string,
    params: CustomerListParams ={}
): Promise <CustomerListResponse>{
    const query = new URLSearchParams();

    if (params.search?.trim()) {
        query.append("search", params.search.trim());
    }
    if (params.zone) {
        query.append("zone", params.zone);
    }

    query.set("page", String(params.page ?? 1));
    query.set("page_size", String(params.page_size ?? 20));
    
    const response = await fetch(`${API_URL}/customers?${query.toString()}`, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
        cache: "no-store",
    });

    if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const detail =
            typeof body.detail === "string"
                ? body.detail
                : "Impossible de charger la liste des clients.";
        throw new Error(detail);
    }
    return response.json();
}