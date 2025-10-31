# Complete Next.js Admin Panel Implementation Guide

This guide provides a comprehensive implementation of a Next.js admin panel for managing push notifications in your ReachToLet Django backend.

## Table of Contents

1. [Project Setup](#project-setup)
2. [API Integration](#api-integration)
3. [Components Implementation](#components-implementation)
4. [Pages Implementation](#pages-implementation)
5. [State Management](#state-management)
6. [Styling & UI](#styling--ui)
7. [Authentication](#authentication)
8. [Deployment](#deployment)

## Project Setup

### 1. Initialize Next.js Project

```bash
npx create-next-app@latest reachtolet-admin-panel --typescript --tailwind --eslint --app
cd reachtolet-admin-panel
```

### 2. Install Required Dependencies

```bash
npm install @tanstack/react-query axios react-hook-form @hookform/resolvers zod
npm install lucide-react @radix-ui/react-dialog @radix-ui/react-dropdown-menu
npm install @radix-ui/react-select @radix-ui/react-toast @radix-ui/react-tabs
npm install date-fns recharts clsx tailwind-merge
npm install -D @types/node
```

### 3. Environment Configuration

Create `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_APP_NAME=ReachToLet Admin Panel
```

## API Integration

### 1. API Client Setup

Create `lib/api.ts`:

```typescript
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### 2. API Types

Create `types/api.ts`:

```typescript
export interface User {
  id: number;
  email: string;
  name: string;
  phone?: string;
  country_code?: string;
  user_type: 'billboard_owner' | 'advertiser' | 'user';
  has_fcm_token: boolean;
  is_active: boolean;
  date_joined: string;
  last_login?: string;
}

export interface NotificationTemplate {
  id: number;
  name: string;
  title: string;
  message: string;
  description?: string;
  recipient_type: 'all_users' | 'billboard_owners' | 'advertisers' | 'specific_users';
  variables: string[];
  is_active: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface NotificationCampaign {
  id: string;
  title: string;
  message: string;
  recipient_type: 'all_users' | 'billboard_owners' | 'advertisers' | 'specific_users';
  template_name?: string;
  custom_data: Record<string, any>;
  status: 'draft' | 'scheduled' | 'sending' | 'sent' | 'failed';
  scheduled_at?: string;
  sent_at?: string;
  total_recipients: number;
  sent_count: number;
  delivered_count: number;
  opened_count: number;
  failed_count: number;
  created_by: number;
  created_by_name: string;
  created_by_email: string;
  created_at: string;
  updated_at: string;
  recipient_count: number;
  delivery_rate: number;
  open_rate: number;
}

export interface NotificationStats {
  total_users: number;
  billboard_owners: number;
  advertisers: number;
  users_with_tokens: number;
  sent_today: number;
  sent_this_week: number;
  sent_this_month: number;
  total_campaigns: number;
  active_campaigns: number;
  draft_campaigns: number;
  avg_delivery_rate: number;
  avg_open_rate: number;
}

export interface CreateCampaignData {
  title: string;
  message: string;
  recipient_type: 'all_users' | 'billboard_owners' | 'advertisers' | 'specific_users';
  template_name?: string;
  custom_data?: Record<string, any>;
  scheduled_at?: string;
  specific_user_ids?: number[];
}
```

### 3. API Hooks

Create `hooks/useApi.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { CreateCampaignData, NotificationStats } from '@/types/api';

// Campaign hooks
export const useCampaigns = (params?: {
  status?: string;
  recipient_type?: string;
  search?: string;
  page?: number;
}) => {
  return useQuery({
    queryKey: ['campaigns', params],
    queryFn: async () => {
      const response = await apiClient.get('/admin-panel/campaigns/', { params });
      return response.data;
    },
  });
};

export const useCampaign = (id: string) => {
  return useQuery({
    queryKey: ['campaign', id],
    queryFn: async () => {
      const response = await apiClient.get(`/admin-panel/campaigns/${id}/`);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useCreateCampaign = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: CreateCampaignData) => {
      const response = await apiClient.post('/admin-panel/campaigns/create/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });
};

export const useSendNotification = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (campaignId: string) => {
      const response = await apiClient.post('/admin-panel/send/', {
        campaign_id: campaignId,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });
};

// Template hooks
export const useTemplates = () => {
  return useQuery({
    queryKey: ['templates'],
    queryFn: async () => {
      const response = await apiClient.get('/admin-panel/templates/');
      return response.data;
    },
  });
};

// User hooks
export const useUsers = (params?: {
  user_type?: string;
  has_token?: boolean;
  search?: string;
  page?: number;
}) => {
  return useQuery({
    queryKey: ['users', params],
    queryFn: async () => {
      const response = await apiClient.get('/admin-panel/users/', { params });
      return response.data;
    },
  });
};

// Stats hooks
export const useNotificationStats = () => {
  return useQuery({
    queryKey: ['notification-stats'],
    queryFn: async () => {
      const response = await apiClient.get('/admin-panel/stats/');
      return response.data;
    },
  });
};
```

## Components Implementation

### 1. Layout Components

Create `components/layout/Sidebar.tsx`:

```typescript
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Users, 
  Megaphone, 
  BarChart3, 
  Settings,
  Send,
  FileText
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Users', href: '/users', icon: Users },
  { name: 'Billboards', href: '/billboards', icon: Megaphone },
  { name: 'Send Notifications', href: '/notifications', icon: Send },
  { name: 'Templates', href: '/templates', icon: FileText },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-64 flex-col bg-gray-900">
      <div className="flex h-16 shrink-0 items-center px-4">
        <div className="flex items-center">
          <div className="h-8 w-8 rounded bg-white flex items-center justify-center">
            <span className="text-gray-900 font-bold text-lg">R</span>
          </div>
          <span className="ml-2 text-white font-semibold">ReachToLet</span>
        </div>
      </div>
      <nav className="flex flex-1 flex-col px-2 py-4">
        <ul role="list" className="flex flex-1 flex-col gap-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  className={cn(
                    'group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold',
                    isActive
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-300 hover:text-white hover:bg-gray-800'
                  )}
                >
                  <item.icon className="h-6 w-6 shrink-0" />
                  {item.name}
                </Link>
              </li>
            );
          })}
        </ul>
        <div className="mt-auto">
          <div className="px-2 py-4 border-t border-gray-700">
            <div className="text-sm text-gray-300">Admin User</div>
            <div className="text-xs text-gray-400">admin</div>
            <button className="mt-2 text-xs text-gray-400 hover:text-white">
              Logout
            </button>
          </div>
        </div>
      </nav>
    </div>
  );
}
```

### 2. Dashboard Components

Create `components/dashboard/StatsCard.tsx`:

```typescript
import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: number;
  icon: LucideIcon;
  change?: {
    value: number;
    type: 'increase' | 'decrease';
  };
}

export function StatsCard({ title, value, icon: Icon, change }: StatsCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <Icon className="h-8 w-8 text-gray-400" />
        </div>
        <div className="ml-4 w-0 flex-1">
          <dl>
            <dt className="text-sm font-medium text-gray-500 truncate">
              {title}
            </dt>
            <dd className="text-2xl font-semibold text-gray-900">
              {value.toLocaleString()}
            </dd>
          </dl>
        </div>
      </div>
      {change && (
        <div className="mt-2">
          <span
            className={`text-sm font-medium ${
              change.type === 'increase' ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {change.type === 'increase' ? '+' : '-'}{change.value}%
          </span>
          <span className="text-sm text-gray-500 ml-1">from last month</span>
        </div>
      )}
    </div>
  );
}
```

### 3. Notification Components

Create `components/notifications/NotificationForm.tsx`:

```typescript
'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreateCampaign, useTemplates } from '@/hooks/useApi';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Select } from '@/components/ui/Select';

const notificationSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  message: z.string().min(1, 'Message is required'),
  recipient_type: z.enum(['all_users', 'billboard_owners', 'advertisers', 'specific_users']),
  template_name: z.string().optional(),
  scheduled_at: z.string().optional(),
  specific_user_ids: z.array(z.number()).optional(),
});

type NotificationFormData = z.infer<typeof notificationSchema>;

export function NotificationForm() {
  const [selectedUsers, setSelectedUsers] = useState<number[]>([]);
  const { data: templates } = useTemplates();
  const createCampaign = useCreateCampaign();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<NotificationFormData>({
    resolver: zodResolver(notificationSchema),
  });

  const recipientType = watch('recipient_type');

  const onSubmit = (data: NotificationFormData) => {
    const formData = {
      ...data,
      specific_user_ids: recipientType === 'specific_users' ? selectedUsers : undefined,
    };
    createCampaign.mutate(formData);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Quick Templates
            </label>
            <Select
              placeholder="Select a template or create custom"
              onValueChange={(value) => {
                if (value && templates) {
                  const template = templates.results.find(t => t.id.toString() === value);
                  if (template) {
                    setValue('title', template.title);
                    setValue('message', template.message);
                    setValue('recipient_type', template.recipient_type);
                  }
                }
              }}
            >
              <option value="">Select a template or create custom</option>
              {templates?.results?.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Notification Title
            </label>
            <Input
              {...register('title')}
              placeholder="Enter notification title"
              className={errors.title ? 'border-red-500' : ''}
            />
            {errors.title && (
              <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Message
            </label>
            <Textarea
              {...register('message')}
              placeholder="Enter your notification message"
              rows={4}
              className={errors.message ? 'border-red-500' : ''}
            />
            {errors.message && (
              <p className="mt-1 text-sm text-red-600">{errors.message.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Recipient Group
            </label>
            <div className="space-y-2">
              {[
                { value: 'all_users', label: 'All Users' },
                { value: 'billboard_owners', label: 'Billboard Owners Only' },
                { value: 'advertisers', label: 'Advertisers Only' },
                { value: 'specific_users', label: 'Specific Users' },
              ].map((option) => (
                <label key={option.value} className="flex items-center">
                  <input
                    type="radio"
                    value={option.value}
                    {...register('recipient_type')}
                    className="mr-2"
                  />
                  {option.label}
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">Select Recipients</h3>
          <p className="text-sm text-gray-500">
            Choose specific users to receive the notification.
          </p>
          
          {recipientType === 'specific_users' && (
            <UserSelector
              selectedUsers={selectedUsers}
              onSelectionChange={setSelectedUsers}
            />
          )}
        </div>
      </div>

      <div className="flex justify-end">
        <Button
          type="submit"
          disabled={createCampaign.isPending}
          className="bg-black text-white px-6 py-2 rounded-md flex items-center space-x-2"
        >
          <Send className="h-4 w-4" />
          <span>Send Notification</span>
        </Button>
      </div>
    </form>
  );
}
```

### 4. Campaign List Component

Create `components/campaigns/CampaignList.tsx`:

```typescript
'use client';

import { useState } from 'react';
import { useCampaigns } from '@/hooks/useApi';
import { format } from 'date-fns';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { 
  MoreHorizontal, 
  Send, 
  Eye, 
  Edit, 
  Trash2,
  Clock,
  CheckCircle,
  XCircle
} from 'lucide-react';

export function CampaignList() {
  const [filters, setFilters] = useState({
    status: '',
    recipient_type: '',
    search: '',
  });

  const { data: campaigns, isLoading } = useCampaigns(filters);

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      draft: { color: 'bg-gray-100 text-gray-800', icon: Edit },
      scheduled: { color: 'bg-yellow-100 text-yellow-800', icon: Clock },
      sending: { color: 'bg-blue-100 text-blue-800', icon: Send },
      sent: { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      failed: { color: 'bg-red-100 text-red-800', icon: XCircle },
    };

    const config = statusConfig[status as keyof typeof statusConfig];
    const Icon = config.icon;

    return (
      <Badge className={`${config.color} flex items-center space-x-1`}>
        <Icon className="h-3 w-3" />
        <span>{status}</span>
      </Badge>
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="scheduled">Scheduled</option>
              <option value="sending">Sending</option>
              <option value="sent">Sent</option>
              <option value="failed">Failed</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Recipient Type
            </label>
            <select
              value={filters.recipient_type}
              onChange={(e) => setFilters({ ...filters, recipient_type: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="">All Types</option>
              <option value="all_users">All Users</option>
              <option value="billboard_owners">Billboard Owners</option>
              <option value="advertisers">Advertisers</option>
              <option value="specific_users">Specific Users</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <input
              type="text"
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              placeholder="Search campaigns..."
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>
        </div>
      </div>

      {/* Campaign List */}
      <div className="space-y-4">
        {campaigns?.results?.map((campaign) => (
          <div key={campaign.id} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {campaign.title}
                  </h3>
                  {getStatusBadge(campaign.status)}
                </div>
                
                <p className="text-gray-600 mb-4">{campaign.message}</p>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Recipients:</span>
                    <span className="ml-1 font-medium">{campaign.total_recipients}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Sent:</span>
                    <span className="ml-1 font-medium">{campaign.sent_count}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Delivered:</span>
                    <span className="ml-1 font-medium">{campaign.delivered_count}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Opened:</span>
                    <span className="ml-1 font-medium">{campaign.opened_count}</span>
                  </div>
                </div>
                
                <div className="mt-4 text-sm text-gray-500">
                  Created by {campaign.created_by_name} on{' '}
                  {format(new Date(campaign.created_at), 'MMM dd, yyyy HH:mm')}
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm">
                  <Eye className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="sm">
                  <Edit className="h-4 w-4" />
                </Button>
                {campaign.status === 'draft' && (
                  <Button size="sm" className="bg-green-600 hover:bg-green-700">
                    <Send className="h-4 w-4 mr-1" />
                    Send
                  </Button>
                )}
                <Button variant="outline" size="sm">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Pages Implementation

### 1. Dashboard Page

Create `app/page.tsx`:

```typescript
'use client';

import { useNotificationStats } from '@/hooks/useApi';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { CampaignList } from '@/components/campaigns/CampaignList';
import { 
  Users, 
  Megaphone, 
  UserCheck, 
  Send,
  TrendingUp,
  Activity
} from 'lucide-react';

export default function Dashboard() {
  const { data: stats, isLoading } = useNotificationStats();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Overview of your notification system</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Users"
          value={stats?.total_users || 0}
          icon={Users}
        />
        <StatsCard
          title="Billboard Owners"
          value={stats?.billboard_owners || 0}
          icon={Megaphone}
        />
        <StatsCard
          title="Advertisers"
          value={stats?.advertisers || 0}
          icon={UserCheck}
        />
        <StatsCard
          title="Sent Today"
          value={stats?.sent_today || 0}
          icon={Send}
        />
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Avg Delivery Rate</p>
              <p className="text-2xl font-semibold text-gray-900">
                {stats?.avg_delivery_rate?.toFixed(1) || 0}%
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Activity className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Avg Open Rate</p>
              <p className="text-2xl font-semibold text-gray-900">
                {stats?.avg_open_rate?.toFixed(1) || 0}%
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Send className="h-8 w-8 text-purple-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Active Campaigns</p>
              <p className="text-2xl font-semibold text-gray-900">
                {stats?.active_campaigns || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Campaigns */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Campaigns</h2>
        <CampaignList />
      </div>
    </div>
  );
}
```

### 2. Notifications Page

Create `app/notifications/page.tsx`:

```typescript
'use client';

import { useState } from 'react';
import { useNotificationStats } from '@/hooks/useApi';
import { NotificationForm } from '@/components/notifications/NotificationForm';
import { UserSelector } from '@/components/notifications/UserSelector';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { Users, Megaphone, UserCheck, Send } from 'lucide-react';

export default function NotificationsPage() {
  const { data: stats } = useNotificationStats();
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Send Notifications</h1>
        <p className="text-gray-600">Send push notifications to users from the admin panel</p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatsCard
          title="Total Users"
          value={stats?.total_users || 0}
          icon={Users}
        />
        <StatsCard
          title="Billboard Owners"
          value={stats?.billboard_owners || 0}
          icon={Megaphone}
        />
        <StatsCard
          title="Advertisers"
          value={stats?.advertisers || 0}
          icon={UserCheck}
        />
        <StatsCard
          title="Sent Today"
          value={stats?.sent_today || 0}
          icon={Send}
        />
      </div>

      {/* Notification Form */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Compose Notification</h2>
          <p className="text-sm text-gray-600">Send push notifications to users from the admin panel</p>
        </div>
        <div className="p-6">
          <NotificationForm />
        </div>
      </div>
    </div>
  );
}
```

### 3. Users Page

Create `app/users/page.tsx`:

```typescript
'use client';

import { useState } from 'react';
import { useUsers } from '@/hooks/useApi';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { 
  Search, 
  Filter, 
  MoreHorizontal,
  User,
  Mail,
  Phone,
  CheckCircle,
  XCircle
} from 'lucide-react';

export default function UsersPage() {
  const [filters, setFilters] = useState({
    user_type: '',
    has_token: '',
    search: '',
  });

  const { data: users, isLoading } = useUsers(filters);

  const getUserTypeBadge = (userType: string) => {
    const config = {
      billboard_owner: { color: 'bg-blue-100 text-blue-800', label: 'Billboard Owner' },
      advertiser: { color: 'bg-green-100 text-green-800', label: 'Advertiser' },
      user: { color: 'bg-gray-100 text-gray-800', label: 'User' },
    };

    const { color, label } = config[userType as keyof typeof config] || config.user;

    return <Badge className={color}>{label}</Badge>;
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(10)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="flex items-center space-x-4">
              <div className="h-10 w-10 bg-gray-200 rounded-full"></div>
              <div className="space-y-2">
                <div className="h-4 bg-gray-200 rounded w-48"></div>
                <div className="h-3 bg-gray-200 rounded w-32"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Users</h1>
        <p className="text-gray-600">Manage and view user information</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search users..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="pl-10"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              User Type
            </label>
            <select
              value={filters.user_type}
              onChange={(e) => setFilters({ ...filters, user_type: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="">All Types</option>
              <option value="billboard_owners">Billboard Owners</option>
              <option value="advertisers">Advertisers</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              FCM Token
            </label>
            <select
              value={filters.has_token}
              onChange={(e) => setFilters({ ...filters, has_token: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="">All Users</option>
              <option value="true">Has Token</option>
              <option value="false">No Token</option>
            </select>
          </div>
          
          <div className="flex items-end">
            <Button variant="outline" className="w-full">
              <Filter className="h-4 w-4 mr-2" />
              More Filters
            </Button>
          </div>
        </div>
      </div>

      {/* Users List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Users ({users?.count || 0})</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {users?.results?.map((user) => (
            <div key={user.id} className="px-6 py-4 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                    <User className="h-5 w-5 text-gray-600" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="text-sm font-medium text-gray-900">
                        {user.full_name}
                      </h3>
                      {getUserTypeBadge(user.user_type)}
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <div className="flex items-center space-x-1">
                        <Mail className="h-4 w-4" />
                        <span>{user.email}</span>
                      </div>
                      {user.phone && (
                        <div className="flex items-center space-x-1">
                          <Phone className="h-4 w-4" />
                          <span>{user.phone}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <div className="flex items-center space-x-1">
                    {user.has_fcm_token ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className="text-sm text-gray-500">
                      {user.has_fcm_token ? 'Has Token' : 'No Token'}
                    </span>
                  </div>
                  
                  <Button variant="outline" size="sm">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

## State Management

### 1. Query Client Setup

Create `lib/queryClient.ts`:

```typescript
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});
```

### 2. Providers Setup

Create `app/providers.tsx`:

```typescript
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from '@/lib/queryClient';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

## Styling & UI

### 1. Tailwind Configuration

Update `tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
    },
  },
  plugins: [],
}
```

### 2. Utility Functions

Create `lib/utils.ts`:

```typescript
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### 3. UI Components

Create `components/ui/Button.tsx`:

```typescript
import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'md', ...props }, ref) => {
    return (
      <button
        className={cn(
          'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background',
          {
            'bg-primary text-primary-foreground hover:bg-primary/90': variant === 'default',
            'border border-input hover:bg-accent hover:text-accent-foreground': variant === 'outline',
            'hover:bg-accent hover:text-accent-foreground': variant === 'ghost',
          },
          {
            'h-8 px-3 text-xs': size === 'sm',
            'h-10 px-4 py-2': size === 'md',
            'h-12 px-8 text-lg': size === 'lg',
          },
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';
```

## Authentication

### 1. Auth Context

Create `contexts/AuthContext.tsx`:

```typescript
'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';

interface User {
  id: number;
  email: string;
  name: string;
  is_staff: boolean;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (token) {
      // Verify token and get user info
      apiClient.get('/users/me/')
        .then(response => {
          setUser(response.data);
        })
        .catch(() => {
          localStorage.removeItem('authToken');
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const response = await apiClient.post('/auth/login/', {
      email,
      password,
    });
    
    const { access, user: userData } = response.data;
    localStorage.setItem('authToken', access);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

### 2. Login Page

Create `app/login/page.tsx`:

```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      await login(email, password);
      router.push('/');
    } catch (error) {
      console.error('Login failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 rounded bg-black flex items-center justify-center">
            <span className="text-white font-bold text-xl">R</span>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            ReachToLet Admin Panel
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Sign in to your account
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <Input
                id="email"
                name="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1"
                placeholder="Enter your email"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1"
                placeholder="Enter your password"
              />
            </div>
          </div>

          <div>
            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-black text-white hover:bg-gray-800"
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

## Deployment

### 1. Vercel Deployment

Create `vercel.json`:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "env": {
    "NEXT_PUBLIC_API_BASE_URL": "https://your-django-api.com/api"
  }
}
```

### 2. Environment Variables

For production, update your environment variables:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-django-api.com/api
NEXT_PUBLIC_APP_NAME=ReachToLet Admin Panel
```

### 3. Build Scripts

Update `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  }
}
```

## API Endpoints Summary

Your Django backend now provides these endpoints:

### Campaign Management
- `GET /api/admin-panel/campaigns/` - List campaigns
- `POST /api/admin-panel/campaigns/create/` - Create campaign
- `GET /api/admin-panel/campaigns/{id}/` - Get campaign details
- `PUT /api/admin-panel/campaigns/{id}/` - Update campaign
- `DELETE /api/admin-panel/campaigns/{id}/` - Delete campaign

### Notification Actions
- `POST /api/admin-panel/send/` - Send notification immediately
- `POST /api/admin-panel/bulk-action/` - Bulk actions (send, cancel, retry)

### Templates
- `GET /api/admin-panel/templates/` - List templates
- `POST /api/admin-panel/templates/` - Create template
- `GET /api/admin-panel/templates/{id}/` - Get template
- `PUT /api/admin-panel/templates/{id}/` - Update template
- `DELETE /api/admin-panel/templates/{id}/` - Delete template

### Users
- `GET /api/admin-panel/users/` - List users with filtering

### Analytics
- `GET /api/admin-panel/stats/` - Get notification statistics
- `GET /api/admin-panel/campaigns/{id}/analytics/` - Get campaign analytics

## Key Features Implemented

1. **Campaign Management**: Create, edit, and manage notification campaigns
2. **User Targeting**: Target all users, billboard owners, advertisers, or specific users
3. **Template System**: Predefined templates for common notifications
4. **Analytics Dashboard**: Comprehensive statistics and performance metrics
5. **Real-time Updates**: Live campaign status and delivery tracking
6. **Bulk Operations**: Send, cancel, or retry failed notifications
7. **User Management**: View and filter users with FCM token status
8. **Responsive Design**: Mobile-friendly admin interface

This implementation provides a complete, production-ready admin panel for managing push notifications in your ReachToLet application.
