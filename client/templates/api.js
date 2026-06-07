// API client for Sports Day '26 Full Stack application
const API_BASE_URL = 'http://localhost:5000/api';

/**
 * Helper to perform fetch requests with JSON parsing and error handling.
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    // Ensure JSON content-type if body is passed
    if (options.body && typeof options.body === 'object') {
        options.body = JSON.stringify(options.body);
        options.headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };
    }
    
    // Enable cookies/sessions sharing
    options.credentials = 'include';
    
    const response = await fetch(url, options);
    
    if (!response.ok) {
        let errMsg = `Request failed with status ${response.status}`;
        try {
            const data = await response.json();
            errMsg = data.message || data.error || errMsg;
        } catch (e) {}
        throw new Error(errMsg);
    }
    
    return await response.json();
}

/**
 * Auth API Blueprint Client
 */
const AuthAPI = {
    async login(username, password) {
        const response = await apiRequest('/auth/login', {
            method: 'POST',
            body: { username, password }
        });
        // Persist session to localStorage so file:// dashboards can read it
        // (cookies from localhost:5000 are not shared with file:// pages)
        if (response.success && response.user) {
            localStorage.setItem('sd_session', JSON.stringify(response.user));
        }
        return response;
    },
    async logout() {
        localStorage.removeItem('sd_session');
        try {
            return await apiRequest('/auth/logout', { method: 'POST' });
        } catch (e) {
            return { success: true };
        }
    },
    async getSession() {
        // First check localStorage (works for file:// pages)
        const stored = localStorage.getItem('sd_session');
        if (stored) {
            try {
                const user = JSON.parse(stored);
                return { authenticated: true, user };
            } catch (e) {}
        }
        // Fallback: try server session (works when served via http://)
        try {
            return await apiRequest('/auth/session');
        } catch (err) {
            return { authenticated: false };
        }
    },
    async createUser(userData) {
        return await apiRequest('/auth/create-user', {
            method: 'POST',
            body: userData
        });
    }
};

/**
 * Events API Client
 */
const EventsAPI = {
    async getAll() {
        try {
            return await apiRequest('/events');
        } catch (err) {
            console.warn("API Events fetch failed, using fallback static data.", err);
            // Static fallback
            return [
                { id: "sprint", displayName: "100m Sprint Championship", type: "solo", image: "100m_Sprint.jpg.jpeg" },
                { id: "sprint200m", displayName: "200m Sprint", type: "solo", image: "200m_Sprint.jpg.jpeg" },
                { id: "highjump", displayName: "High Jump", type: "solo", image: "High_Jump.jpg.jpeg" },
                { id: "longjump", displayName: "Long Jump", type: "solo", image: "Long_Jump.jpg.jpeg" },
                { id: "badminton", displayName: "Badminton Singles", type: "solo", image: "Badminton_Singles.jpg.jpeg" },
                { id: "basketball", displayName: "Basketball", type: "team", image: "BasketBall.jpg.jpeg" },
                { id: "football", displayName: "Football", type: "team", image: "Football.jpg.jpeg" },
                { id: "cricket", displayName: "Cricket", type: "team", image: "Cricket.jpg.jpeg" },
                { id: "volleyball", displayName: "Volleyball", type: "team", image: "VolleyBall.jpg.jpeg" }
            ];
        }
    },
    async get(id) {
        try {
            return await apiRequest(`/events/${id}`);
        } catch (err) {
            console.warn(`API Event fetch failed for ID: ${id}, using local search.`, err);
            const events = await this.getAll();
            return events.find(e => e.id === id) || null;
        }
    },
    async create(eventData) {
        try {
            return await apiRequest('/events', {
                method: 'POST',
                body: eventData
            });
        } catch (err) {
            console.warn("API Event creation failed, simulating locally.", err);
            const localEvents = JSON.parse(localStorage.getItem('events') || '[]');
            const mockEvent = {
                id: eventData.id,
                displayName: eventData.name,
                type: eventData.name.toLowerCase() in ["football", "basketball", "volleyball", "cricket"] ? "team" : "solo",
                image: `${eventData.id}.jpg.jpeg`,
                description: `${eventData.name} tournament.`,
                date: eventData.date,
                time: "09:00 AM",
                venue: eventData.venue,
                status: eventData.status
            };
            localEvents.push(mockEvent);
            localStorage.setItem('events', JSON.stringify(localEvents));
            return {
                success: true,
                message: "Event created successfully! (Offline Mode)",
                event: mockEvent
            };
        }
    }
};

/**
 * Registrations API Client
 */
const RegistrationsAPI = {
    async getAll() {
        return await apiRequest('/registrations');
    },
    async create(regData) {
        return await apiRequest('/registrations', {
            method: 'POST',
            body: regData
        });
    },
    async delete(id) {
        return await apiRequest(`/registrations/${id}`, { method: 'DELETE' });
    }
};

/**
 * Results/Leaderboard API Client
 */
const ResultsAPI = {
    async getAll() {
        return await apiRequest('/results');
    },
    async create(resultData) {
        try {
            return await apiRequest('/results', {
                method: 'POST',
                body: resultData
            });
        } catch (err) {
            console.error("API Results creation failed.", err);
            throw err;
        }
    }
};

/**
 * Scores API Client
 */
const ScoresAPI = {
    async getAll() {
        try {
            return await apiRequest('/scores');
        } catch (err) {
            console.warn("API Scores fetch failed, returning empty list.", err);
            return [];
        }
    },
    async create(scoreData) {
        try {
            return await apiRequest('/scores', {
                method: 'POST',
                body: scoreData
            });
        } catch (err) {
            console.error("API Scores creation failed.", err);
            throw err;
        }
    }
};

/**
 * Departments Management API Client
 */
const DepartmentsAPI = {
    async getAll() {
        try {
            return await apiRequest('/auth/departments');
        } catch (err) {
            console.warn("API Departments fetch failed, using local storage fallback.", err);
            return JSON.parse(localStorage.getItem('departments') || '[]');
        }
    },
    async create(deptData) {
        try {
            return await apiRequest('/auth/register-dept', {
                method: 'POST',
                body: deptData
            });
        } catch (err) {
            console.warn("API Departments registration failed, simulating locally.", err);
            const localDepts = JSON.parse(localStorage.getItem('departments') || '[]');
            const mockDeptId = '26SD' + Math.floor(100 + Math.random() * 900);
            const mockUsername = deptData.department.toLowerCase().replace(/[^a-z0-9]/g, '_') + '_coord';
            const mockPassword = 'MOCK' + Math.random().toString(36).substr(2, 5).toUpperCase();
            
            const normalizedDept = {
                deptId: mockDeptId,
                name: deptData.department,
                coordinator: deptData.coordinatorName,
                email: deptData.email,
                phone: deptData.phone,
                totalStudents: deptData.totalStudents || 0,
                shift: deptData.shift || 'Shift-I',
                username: mockUsername,
                password: mockPassword
            };
            
            localDepts.push(normalizedDept);
            localStorage.setItem('departments', JSON.stringify(localDepts));
            
            return {
                success: true,
                message: "Department registered and coordinator login created successfully! (Offline Mode)",
                username: mockUsername,
                password: mockPassword,
                deptId: mockDeptId
            };
        }
    },
    async registerManager(managerData) {
        try {
            return await apiRequest('/auth/register-manager', {
                method: 'POST',
                body: managerData
            });
        } catch (err) {
            console.warn("API Manager registration failed, simulating locally.", err);
            const localDepts = JSON.parse(localStorage.getItem('departments') || '[]');
            const mockUsername = managerData.department.toLowerCase().replace(/[^a-z0-9]/g, '_') + '_' + (managerData.inCharge || 'general').toLowerCase().replace(/[^a-z0-9]/g, '_') + '_coord';
            const mockPassword = 'MOCK' + Math.random().toString(36).substr(2, 5).toUpperCase();
            
            const normalizedDept = {
                deptId: managerData.staffId,
                name: managerData.department,
                coordinator: managerData.coordinatorName,
                phone: managerData.phone,
                shift: managerData.shift || 'Shift-I',
                inCharge: managerData.inCharge || 'General',
                username: mockUsername,
                password: mockPassword,
                role: 'event'
            };
            
            localDepts.push(normalizedDept);
            localStorage.setItem('departments', JSON.stringify(localDepts));
            
            return {
                success: true,
                message: "Event manager registered and login details created successfully! (Offline Mode)",
                username: mockUsername,
                password: mockPassword,
                deptId: managerData.staffId
            };
        }
    }
};
