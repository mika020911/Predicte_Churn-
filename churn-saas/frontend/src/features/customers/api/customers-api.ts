import type {
    CustomerDetail,
    CustomerListParams,
    CustomerListResponse,
    SimulationPayload,
    SimulationResult,
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

export async function getCustomer(
    token: string,
    customerId: number,
): Promise<CustomerDetail> {
    const response = await fetch(`${API_URL}/customers/${customerId}`, {
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
                : "Impossible de charger la fiche du client.";
        throw new Error(detail);
    }

    return response.json();
}
export async function simulateCustomer(
    token: string,
    customerId: number,
    payload: SimulationPayload,
): Promise<SimulationResult> {
    const response = await fetch(
        `${API_URL}/customers/${customerId}/simulate`,
        {
            method: "POST",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        },
    );

    if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const detail =
            typeof body.detail === "string"
                ? body.detail
                : "Impossible de simuler un nouveau score.";
        throw new Error(detail);
    }

    return response.json();
}
