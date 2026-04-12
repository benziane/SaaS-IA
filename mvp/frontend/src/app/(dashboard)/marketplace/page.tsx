'use client';

import { useState } from 'react';
import {
  Plus, Search, Store, Download, Trash2, Upload, CircleOff,
  Star, Bot, Gauge, Pencil, BarChart3, Image, Shield,
  RefreshCw, Tags, User, Package, Loader2,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Separator } from '@/lib/design-hub/components/Separator';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/lib/design-hub/components/Select';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/lib/design-hub/components/Dialog';

import {
  useAddReview,
  useCreateListing,
  useDeleteListing,
  useInstallListing,
  useMarketplaceCategories,
  useMarketplaceFeatured,
  useMarketplaceListings,
  useMyListings,
  usePublishListing,
  useUnpublishListing,
} from '@/features/marketplace/hooks/useMarketplace';
import type { MarketplaceListing } from '@/features/marketplace/types';

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  ai: <Bot className="h-4 w-4" />,
  productivity: <Gauge className="h-4 w-4" />,
  content: <Pencil className="h-4 w-4" />,
  data: <BarChart3 className="h-4 w-4" />,
  // eslint-disable-next-line jsx-a11y/alt-text
  media: <Image className="h-4 w-4" />,
  security: <Shield className="h-4 w-4" />,
  automation: <RefreshCw className="h-4 w-4" />,
  other: <Tags className="h-4 w-4" />,
};

const TYPE_VARIANTS: Record<string, 'default' | 'secondary' | 'success' | 'warning'> = {
  module: 'default',
  template: 'secondary',
  prompt: 'success',
  workflow: 'warning',
  dataset: 'default',
};

const LISTING_TYPES = ['module', 'template', 'prompt', 'workflow', 'dataset'];
const LISTING_CATEGORIES = ['ai', 'productivity', 'content', 'data', 'media', 'security', 'automation', 'other'];
const SORT_OPTIONS = [
  { value: 'newest', label: 'Newest' },
  { value: 'popular', label: 'Most Popular' },
  { value: 'rating', label: 'Top Rated' },
  { value: 'price_asc', label: 'Price: Low to High' },
  { value: 'price_desc', label: 'Price: High to Low' },
];

function StarRating({ value }: { value: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((s) => (
        <Star
          key={s}
          className={`h-3.5 w-3.5 ${s <= Math.round(value) ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
        />
      ))}
    </div>
  );
}

export default function MarketplacePage() {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>();
  const [selectedType, setSelectedType] = useState<string | undefined>();
  const [sortBy, setSortBy] = useState('newest');
  const [tab, setTab] = useState<'browse' | 'my-listings'>('browse');

  const [createOpen, setCreateOpen] = useState(false);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [reviewListingId, setReviewListingId] = useState<string | null>(null);
  const [reviewRating, setReviewRating] = useState<number | null>(3);
  const [reviewComment, setReviewComment] = useState('');

  // Create form state
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newType, setNewType] = useState('template');
  const [newCategory, setNewCategory] = useState('ai');
  const [newPrice, setNewPrice] = useState('0');
  const [newTags, setNewTags] = useState('');

  const queryParams = {
    search: search || undefined,
    category: selectedCategory,
    type: selectedType,
    sort_by: sortBy,
  };

  const { data: listings, isLoading } = useMarketplaceListings(queryParams);
  const { data: featured } = useMarketplaceFeatured();
  const { data: categories } = useMarketplaceCategories();
  const { data: myListings, isLoading: myListingsLoading } = useMyListings();

  const createMutation = useCreateListing();
  const deleteMutation = useDeleteListing();
  const publishMutation = usePublishListing();
  const unpublishMutation = useUnpublishListing();
  const installMutation = useInstallListing();
  const reviewMutation = useAddReview();

  const handleCreate = () => {
    if (!newTitle.trim() || !newDesc.trim()) return;
    createMutation.mutate(
      {
        title: newTitle,
        description: newDesc,
        type: newType,
        category: newCategory,
        price: parseFloat(newPrice) || 0,
        tags: newTags ? newTags.split(',').map((t) => t.trim()).filter(Boolean) : undefined,
      },
      {
        onSuccess: () => {
          setCreateOpen(false);
          setNewTitle('');
          setNewDesc('');
          setNewType('template');
          setNewCategory('ai');
          setNewPrice('0');
          setNewTags('');
        },
      }
    );
  };

  const handleReviewSubmit = () => {
    if (!reviewListingId || !reviewRating) return;
    reviewMutation.mutate(
      { listingId: reviewListingId, data: { rating: reviewRating, comment: reviewComment || undefined } },
      {
        onSuccess: () => {
          setReviewOpen(false);
          setReviewListingId(null);
          setReviewRating(3);
          setReviewComment('');
        },
      }
    );
  };

  const renderListingCard = (listing: MarketplaceListing) => (
    <div key={listing.id} className="col-span-1">
      <div className="surface-card p-5 h-full flex flex-col transition-shadow hover:shadow-lg">
        <div className="flex-1">
          <div className="flex justify-between items-start mb-2">
            <Badge variant={TYPE_VARIANTS[listing.type] || 'default'}>{listing.type}</Badge>
            <span className={`text-sm font-bold ${listing.price === 0 ? 'text-green-600' : 'text-[var(--text-high)]'}`}>
              {listing.price === 0 ? 'Free' : `$${listing.price.toFixed(2)}`}
            </span>
          </div>
          <h3 className="text-lg font-semibold text-[var(--text-high)] truncate mb-1">{listing.title}</h3>
          <p className="text-sm text-[var(--text-mid)] mb-2 line-clamp-2">{listing.description}</p>
          <div className="flex items-center gap-1 mb-2">
            <StarRating value={listing.rating} />
            <span className="text-xs text-[var(--text-mid)]">({listing.reviews_count})</span>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {CATEGORY_ICONS[listing.category] as React.ReactElement || null}
              <span className="ml-1">{listing.category}</span>
            </Badge>
            <span className="text-xs text-[var(--text-mid)]">v{listing.version}</span>
          </div>
          {listing.tags.length > 0 && (
            <div className="mt-2 flex gap-1 flex-wrap">
              {listing.tags.slice(0, 3).map((tag) => (
                <Badge key={tag} variant="outline" className="text-[0.65rem] h-5">{tag}</Badge>
              ))}
            </div>
          )}
        </div>
        <Separator className="my-3" />
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-1">
            <User className="h-3.5 w-3.5 text-[var(--text-mid)]" />
            <span className="text-xs text-[var(--text-mid)]">{listing.author_name}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-xs text-[var(--text-mid)]">{listing.installs_count} installs</span>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    title="Install"
                    className="p-1 rounded hover:bg-[var(--bg-hover)] text-[var(--accent)]"
                    onClick={() => installMutation.mutate(listing.id)}
                    disabled={installMutation.isPending}
                  >
                    <Download className="h-4 w-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent>Install</TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    title="Review"
                    className="p-1 rounded hover:bg-[var(--bg-hover)]"
                    onClick={() => {
                      setReviewListingId(listing.id);
                      setReviewOpen(true);
                    }}
                  >
                    <Star className="h-4 w-4 text-[var(--text-mid)]" />
                  </button>
                </TooltipTrigger>
                <TooltipContent>Review</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
      </div>
    </div>
  );

  const renderMyListingCard = (listing: MarketplaceListing) => (
    <div key={listing.id} className="col-span-1">
      <div className="surface-card p-5 h-full flex flex-col">
        <div className="flex-1">
          <div className="flex justify-between mb-2">
            <Badge variant={TYPE_VARIANTS[listing.type] || 'default'}>{listing.type}</Badge>
            <Badge variant={listing.is_published ? 'success' : 'default'}>
              {listing.is_published ? 'Published' : 'Draft'}
            </Badge>
          </div>
          <h3 className="text-lg font-semibold text-[var(--text-high)] truncate mb-1">{listing.title}</h3>
          <p className="text-sm text-[var(--text-mid)] mb-2 line-clamp-2">{listing.description}</p>
          <div className="flex items-center gap-2">
            <StarRating value={listing.rating} />
            <span className="text-xs text-[var(--text-mid)]">{listing.installs_count} installs</span>
          </div>
        </div>
        <Separator className="my-3" />
        <div className="flex justify-end gap-1">
          <TooltipProvider>
            {listing.is_published ? (
              <Tooltip>
                <TooltipTrigger asChild>
                  <button type="button" title="Unpublish" className="p-1 rounded hover:bg-[var(--bg-hover)]" onClick={() => unpublishMutation.mutate(listing.id)} disabled={unpublishMutation.isPending}>
                    <CircleOff className="h-4 w-4 text-[var(--text-mid)]" />
                  </button>
                </TooltipTrigger>
                <TooltipContent>Unpublish</TooltipContent>
              </Tooltip>
            ) : (
              <Tooltip>
                <TooltipTrigger asChild>
                  <button type="button" title="Publish" className="p-1 rounded hover:bg-green-100 text-green-600" onClick={() => publishMutation.mutate(listing.id)} disabled={publishMutation.isPending}>
                    <Upload className="h-4 w-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent>Publish</TooltipContent>
              </Tooltip>
            )}
            <Tooltip>
              <TooltipTrigger asChild>
                <button type="button" title="Delete" className="p-1 rounded hover:bg-red-100 text-red-500" onClick={() => deleteMutation.mutate(listing.id)} disabled={deleteMutation.isPending}>
                  <Trash2 className="h-4 w-4" />
                </button>
              </TooltipTrigger>
              <TooltipContent>Delete</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-5 space-y-5 animate-enter">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--bg-elevated)] border border-[var(--border)] shrink-0">
            <Store className="h-5 w-5 text-[var(--accent)]" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-high)]">Marketplace</h1>
            <p className="text-xs text-[var(--text-mid)]">Browse and install AI modules</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant={tab === 'browse' ? 'default' : 'outline'}
            onClick={() => setTab('browse')}
          >
            <Store className="h-4 w-4 mr-2" /> Browse
          </Button>
          <Button
            variant={tab === 'my-listings' ? 'default' : 'outline'}
            onClick={() => setTab('my-listings')}
          >
            <Package className="h-4 w-4 mr-2" /> My Listings
          </Button>
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4 mr-2" /> Create Listing
          </Button>
        </div>
      </div>

      {tab === 'browse' ? (
        <div className="grid grid-cols-12 gap-6">
          {/* Sidebar */}
          <div className="col-span-12 md:col-span-2">
            <p className="text-sm font-medium text-[var(--text-high)] mb-2">Categories</p>
            <nav className="space-y-0.5">
              <button
                type="button"
                className={`w-full text-left px-3 py-1.5 rounded text-sm flex items-center gap-2 ${!selectedCategory ? 'bg-[var(--accent)]/10 text-[var(--accent)] font-medium' : 'text-[var(--text-mid)] hover:bg-[var(--bg-hover)]'}`}
                onClick={() => setSelectedCategory(undefined)}
              >
                <Tags className="h-4 w-4" /> All
              </button>
              {(categories || []).map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  className={`w-full text-left px-3 py-1.5 rounded text-sm flex items-center gap-2 ${selectedCategory === cat.id ? 'bg-[var(--accent)]/10 text-[var(--accent)] font-medium' : 'text-[var(--text-mid)] hover:bg-[var(--bg-hover)]'}`}
                  onClick={() => setSelectedCategory(cat.id)}
                >
                  {CATEGORY_ICONS[cat.id] || <Tags className="h-4 w-4" />}
                  {cat.name}
                </button>
              ))}
            </nav>

            <Separator className="my-4" />
            <p className="text-sm font-medium text-[var(--text-high)] mb-2">Type</p>
            <nav className="space-y-0.5">
              <button
                type="button"
                className={`w-full text-left px-3 py-1.5 rounded text-sm ${!selectedType ? 'bg-[var(--accent)]/10 text-[var(--accent)] font-medium' : 'text-[var(--text-mid)] hover:bg-[var(--bg-hover)]'}`}
                onClick={() => setSelectedType(undefined)}
              >
                All Types
              </button>
              {LISTING_TYPES.map((t) => (
                <button
                  key={t}
                  type="button"
                  className={`w-full text-left px-3 py-1.5 rounded text-sm ${selectedType === t ? 'bg-[var(--accent)]/10 text-[var(--accent)] font-medium' : 'text-[var(--text-mid)] hover:bg-[var(--bg-hover)]'}`}
                  onClick={() => setSelectedType(t)}
                >
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </nav>
          </div>

          {/* Main content */}
          <div className="col-span-12 md:col-span-10">
            {/* Search & sort bar */}
            <div className="flex gap-4 mb-6">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-mid)]" />
                <Input
                  className="pl-10"
                  placeholder="Search marketplace..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  {SORT_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Featured section */}
            {!search && !selectedCategory && !selectedType && featured && featured.length > 0 && (
              <div className="mb-8">
                <h2 className="text-lg font-semibold text-[var(--text-high)] flex items-center gap-2 mb-4">
                  <Star className="h-5 w-5 text-yellow-500" /> Featured
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {featured.slice(0, 4).map(renderListingCard)}
                </div>
              </div>
            )}

            {/* Listings grid */}
            {isLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {[...Array(8)].map((_, i) => (
                  <Skeleton key={i} className="h-60 rounded-lg" />
                ))}
              </div>
            ) : listings && listings.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {listings.map(renderListingCard)}
              </div>
            ) : (
              <Alert className="mt-4">
                <AlertDescription>No listings found. Be the first to publish something!</AlertDescription>
              </Alert>
            )}
          </div>
        </div>
      ) : (
        /* My Listings tab */
        <div>
          {myListingsLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {[...Array(3)].map((_, i) => (
                <Skeleton key={i} className="h-52 rounded-lg" />
              ))}
            </div>
          ) : myListings && myListings.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              {myListings.map(renderMyListingCard)}
            </div>
          ) : (
            <Alert>
              <AlertDescription>You have no listings yet. Create your first one!</AlertDescription>
            </Alert>
          )}
        </div>
      )}

      {/* Create listing dialog */}
      <Dialog open={createOpen} onOpenChange={(v) => { if (!v) setCreateOpen(false); }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Create Listing</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 mt-2">
            <Input placeholder="Title" value={newTitle} onChange={(e) => setNewTitle(e.target.value)} />
            <Textarea placeholder="Description" rows={3} value={newDesc} onChange={(e) => setNewDesc(e.target.value)} />
            <div>
              <label className="text-xs text-[var(--text-mid)] mb-1 block">Type</label>
              <Select value={newType} onValueChange={setNewType}>
                <SelectTrigger>
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  {LISTING_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs text-[var(--text-mid)] mb-1 block">Category</label>
              <Select value={newCategory} onValueChange={setNewCategory}>
                <SelectTrigger>
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  {LISTING_CATEGORIES.map((c) => (
                    <SelectItem key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Input type="number" placeholder="Price (USD, 0 = free)" value={newPrice} onChange={(e) => setNewPrice(e.target.value)} />
            <Input placeholder="Tags (comma separated, e.g., seo, automation, ai)" value={newTags} onChange={(e) => setNewTags(e.target.value)} />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button
              onClick={handleCreate}
              disabled={!newTitle.trim() || !newDesc.trim() || createMutation.isPending}
            >
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Review dialog */}
      <Dialog open={reviewOpen} onOpenChange={(v) => { if (!v) setReviewOpen(false); }}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Add Review</DialogTitle>
          </DialogHeader>
          <div className="flex justify-center my-4">
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((s) => (
                <button
                  key={s}
                  type="button"
                  title={`${s} star${s > 1 ? 's' : ''}`}
                  onClick={() => setReviewRating(s)}
                  className="p-0.5"
                >
                  <Star
                    className={`h-7 w-7 ${s <= (reviewRating ?? 0) ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
                  />
                </button>
              ))}
            </div>
          </div>
          <Textarea
            placeholder="Comment (optional)"
            rows={3}
            value={reviewComment}
            onChange={(e) => setReviewComment(e.target.value)}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setReviewOpen(false)}>Cancel</Button>
            <Button
              onClick={handleReviewSubmit}
              disabled={!reviewRating || reviewMutation.isPending}
            >
              {reviewMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Submit'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Error / success alerts */}
      {installMutation.isError && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{installMutation.error?.message || 'Install failed. It may already be installed.'}</AlertDescription>
        </Alert>
      )}
      {installMutation.isSuccess && (
        <Alert className="mt-4">
          <AlertDescription>Listing installed successfully!</AlertDescription>
        </Alert>
      )}
      {reviewMutation.isError && (
        <Alert variant="destructive" className="mt-4">
          <AlertDescription>{reviewMutation.error?.message || 'Review failed.'}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
