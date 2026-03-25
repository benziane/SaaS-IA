'use client';

import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  Grid,
  IconButton,
  InputAdornment,
  InputLabel,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Rating,
  Select,
  Skeleton,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import StorefrontIcon from '@mui/icons-material/Storefront';
import DownloadIcon from '@mui/icons-material/Download';
import DeleteIcon from '@mui/icons-material/Delete';
import PublishIcon from '@mui/icons-material/Publish';
import UnpublishedIcon from '@mui/icons-material/Unpublished';
import StarIcon from '@mui/icons-material/Star';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import SpeedIcon from '@mui/icons-material/Speed';
import EditIcon from '@mui/icons-material/Edit';
import BarChartIcon from '@mui/icons-material/BarChart';
import ImageIcon from '@mui/icons-material/Image';
import ShieldIcon from '@mui/icons-material/Shield';
import AutoModeIcon from '@mui/icons-material/AutoMode';
import CategoryIcon from '@mui/icons-material/Category';
import PersonIcon from '@mui/icons-material/Person';
import InventoryIcon from '@mui/icons-material/Inventory';

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
  ai: <SmartToyIcon fontSize="small" />,
  productivity: <SpeedIcon fontSize="small" />,
  content: <EditIcon fontSize="small" />,
  data: <BarChartIcon fontSize="small" />,
  media: <ImageIcon fontSize="small" />,
  security: <ShieldIcon fontSize="small" />,
  automation: <AutoModeIcon fontSize="small" />,
  other: <CategoryIcon fontSize="small" />,
};

const TYPE_COLORS: Record<string, 'primary' | 'secondary' | 'success' | 'warning' | 'info'> = {
  module: 'primary',
  template: 'secondary',
  prompt: 'success',
  workflow: 'warning',
  dataset: 'info',
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
    <Grid item xs={12} sm={6} md={4} lg={3} key={listing.id}>
      <Card
        sx={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          transition: 'box-shadow 0.2s',
          '&:hover': { boxShadow: 6 },
        }}
      >
        <CardContent sx={{ flexGrow: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
            <Chip
              label={listing.type}
              size="small"
              color={TYPE_COLORS[listing.type] || 'default'}
              variant="outlined"
            />
            <Typography variant="subtitle2" color={listing.price === 0 ? 'success.main' : 'text.primary'} fontWeight="bold">
              {listing.price === 0 ? 'Free' : `$${listing.price.toFixed(2)}`}
            </Typography>
          </Box>
          <Typography variant="h6" gutterBottom noWrap>
            {listing.title}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {listing.description}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 1 }}>
            <Rating value={listing.rating} precision={0.5} size="small" readOnly />
            <Typography variant="caption" color="text.secondary">
              ({listing.reviews_count})
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              label={listing.category}
              size="small"
              icon={CATEGORY_ICONS[listing.category] as React.ReactElement || undefined}
              variant="outlined"
              sx={{ fontSize: '0.7rem' }}
            />
            <Typography variant="caption" color="text.secondary">
              v{listing.version}
            </Typography>
          </Box>
          {listing.tags.length > 0 && (
            <Box sx={{ mt: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
              {listing.tags.slice(0, 3).map((tag) => (
                <Chip key={tag} label={tag} size="small" variant="outlined" sx={{ fontSize: '0.65rem', height: 20 }} />
              ))}
            </Box>
          )}
        </CardContent>
        <Divider />
        <CardActions sx={{ justifyContent: 'space-between', px: 2, py: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <PersonIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary">
              {listing.author_name}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography variant="caption" color="text.secondary">
              {listing.installs_count} installs
            </Typography>
            <Tooltip title="Install">
              <IconButton
                size="small"
                color="primary"
                onClick={() => installMutation.mutate(listing.id)}
                disabled={installMutation.isPending}
              >
                <DownloadIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Review">
              <IconButton
                size="small"
                onClick={() => {
                  setReviewListingId(listing.id);
                  setReviewOpen(true);
                }}
              >
                <StarIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </CardActions>
      </Card>
    </Grid>
  );

  const renderMyListingCard = (listing: MarketplaceListing) => (
    <Grid item xs={12} sm={6} md={4} key={listing.id}>
      <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <CardContent sx={{ flexGrow: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Chip label={listing.type} size="small" color={TYPE_COLORS[listing.type] || 'default'} variant="outlined" />
            <Chip
              label={listing.is_published ? 'Published' : 'Draft'}
              size="small"
              color={listing.is_published ? 'success' : 'default'}
            />
          </Box>
          <Typography variant="h6" gutterBottom noWrap>{listing.title}</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
            {listing.description}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Rating value={listing.rating} precision={0.5} size="small" readOnly />
            <Typography variant="caption">{listing.installs_count} installs</Typography>
          </Box>
        </CardContent>
        <Divider />
        <CardActions sx={{ justifyContent: 'flex-end' }}>
          {listing.is_published ? (
            <Tooltip title="Unpublish">
              <IconButton size="small" onClick={() => unpublishMutation.mutate(listing.id)} disabled={unpublishMutation.isPending}>
                <UnpublishedIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          ) : (
            <Tooltip title="Publish">
              <IconButton size="small" color="success" onClick={() => publishMutation.mutate(listing.id)} disabled={publishMutation.isPending}>
                <PublishIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          <Tooltip title="Delete">
            <IconButton size="small" color="error" onClick={() => deleteMutation.mutate(listing.id)} disabled={deleteMutation.isPending}>
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </CardActions>
      </Card>
    </Grid>
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <StorefrontIcon color="primary" /> Marketplace
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Discover and share modules, templates, prompts, workflows, and datasets
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant={tab === 'browse' ? 'contained' : 'outlined'}
            onClick={() => setTab('browse')}
            startIcon={<StorefrontIcon />}
          >
            Browse
          </Button>
          <Button
            variant={tab === 'my-listings' ? 'contained' : 'outlined'}
            onClick={() => setTab('my-listings')}
            startIcon={<InventoryIcon />}
          >
            My Listings
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setCreateOpen(true)}>
            Create Listing
          </Button>
        </Box>
      </Box>

      {tab === 'browse' ? (
        <Grid container spacing={3}>
          {/* Sidebar */}
          <Grid item xs={12} md={2}>
            <Typography variant="subtitle2" gutterBottom>Categories</Typography>
            <List dense disablePadding>
              <ListItemButton
                selected={!selectedCategory}
                onClick={() => setSelectedCategory(undefined)}
                sx={{ borderRadius: 1, mb: 0.5 }}
              >
                <ListItemIcon sx={{ minWidth: 32 }}><CategoryIcon fontSize="small" /></ListItemIcon>
                <ListItemText primary="All" primaryTypographyProps={{ variant: 'body2' }} />
              </ListItemButton>
              {(categories || []).map((cat) => (
                <ListItemButton
                  key={cat.id}
                  selected={selectedCategory === cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  sx={{ borderRadius: 1, mb: 0.5 }}
                >
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    {CATEGORY_ICONS[cat.id] || <CategoryIcon fontSize="small" />}
                  </ListItemIcon>
                  <ListItemText primary={cat.name} primaryTypographyProps={{ variant: 'body2' }} />
                </ListItemButton>
              ))}
            </List>

            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom>Type</Typography>
            <List dense disablePadding>
              <ListItemButton
                selected={!selectedType}
                onClick={() => setSelectedType(undefined)}
                sx={{ borderRadius: 1, mb: 0.5 }}
              >
                <ListItemText primary="All Types" primaryTypographyProps={{ variant: 'body2' }} />
              </ListItemButton>
              {LISTING_TYPES.map((t) => (
                <ListItemButton
                  key={t}
                  selected={selectedType === t}
                  onClick={() => setSelectedType(t)}
                  sx={{ borderRadius: 1, mb: 0.5 }}
                >
                  <ListItemText primary={t.charAt(0).toUpperCase() + t.slice(1)} primaryTypographyProps={{ variant: 'body2' }} />
                </ListItemButton>
              ))}
            </List>
          </Grid>

          {/* Main content */}
          <Grid item xs={12} md={10}>
            {/* Search & sort bar */}
            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
              <TextField
                size="small"
                placeholder="Search marketplace..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                sx={{ flexGrow: 1 }}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
              <FormControl size="small" sx={{ minWidth: 180 }}>
                <InputLabel>Sort by</InputLabel>
                <Select value={sortBy} label="Sort by" onChange={(e) => setSortBy(e.target.value)}>
                  {SORT_OPTIONS.map((opt) => (
                    <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>

            {/* Featured section */}
            {!search && !selectedCategory && !selectedType && featured && featured.length > 0 && (
              <Box sx={{ mb: 4 }}>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <StarIcon color="warning" /> Featured
                </Typography>
                <Grid container spacing={2}>
                  {featured.slice(0, 4).map(renderListingCard)}
                </Grid>
              </Box>
            )}

            {/* Listings grid */}
            {isLoading ? (
              <Grid container spacing={2}>
                {[...Array(8)].map((_, i) => (
                  <Grid item xs={12} sm={6} md={4} lg={3} key={i}>
                    <Skeleton variant="rounded" height={240} />
                  </Grid>
                ))}
              </Grid>
            ) : listings && listings.length > 0 ? (
              <Grid container spacing={2}>
                {listings.map(renderListingCard)}
              </Grid>
            ) : (
              <Alert severity="info" sx={{ mt: 2 }}>
                No listings found. Be the first to publish something!
              </Alert>
            )}
          </Grid>
        </Grid>
      ) : (
        /* My Listings tab */
        <Box>
          {myListingsLoading ? (
            <Grid container spacing={2}>
              {[...Array(3)].map((_, i) => (
                <Grid item xs={12} sm={6} md={4} key={i}>
                  <Skeleton variant="rounded" height={200} />
                </Grid>
              ))}
            </Grid>
          ) : myListings && myListings.length > 0 ? (
            <Grid container spacing={2}>
              {myListings.map(renderMyListingCard)}
            </Grid>
          ) : (
            <Alert severity="info">
              You have no listings yet. Create your first one!
            </Alert>
          )}
        </Box>
      )}

      {/* Create listing dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Listing</DialogTitle>
        <DialogContent>
          <TextField
            label="Title"
            fullWidth
            margin="dense"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
          />
          <TextField
            label="Description"
            fullWidth
            margin="dense"
            multiline
            rows={3}
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
          />
          <FormControl fullWidth margin="dense">
            <InputLabel>Type</InputLabel>
            <Select value={newType} label="Type" onChange={(e) => setNewType(e.target.value)}>
              {LISTING_TYPES.map((t) => (
                <MenuItem key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Category</InputLabel>
            <Select value={newCategory} label="Category" onChange={(e) => setNewCategory(e.target.value)}>
              {LISTING_CATEGORIES.map((c) => (
                <MenuItem key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            label="Price (USD, 0 = free)"
            fullWidth
            margin="dense"
            type="number"
            value={newPrice}
            onChange={(e) => setNewPrice(e.target.value)}
          />
          <TextField
            label="Tags (comma separated)"
            fullWidth
            margin="dense"
            value={newTags}
            onChange={(e) => setNewTags(e.target.value)}
            placeholder="seo, automation, ai"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={!newTitle.trim() || !newDesc.trim() || createMutation.isPending}
          >
            {createMutation.isPending ? <CircularProgress size={20} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Review dialog */}
      <Dialog open={reviewOpen} onClose={() => setReviewOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Add Review</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
            <Rating
              value={reviewRating}
              onChange={(_, value) => setReviewRating(value)}
              size="large"
            />
          </Box>
          <TextField
            label="Comment (optional)"
            fullWidth
            margin="dense"
            multiline
            rows={3}
            value={reviewComment}
            onChange={(e) => setReviewComment(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReviewOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleReviewSubmit}
            disabled={!reviewRating || reviewMutation.isPending}
          >
            {reviewMutation.isPending ? <CircularProgress size={20} /> : 'Submit'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Error alerts */}
      {installMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => installMutation.reset()}>
          {installMutation.error?.message || 'Install failed. It may already be installed.'}
        </Alert>
      )}
      {installMutation.isSuccess && (
        <Alert severity="success" sx={{ mt: 2 }} onClose={() => installMutation.reset()}>
          Listing installed successfully!
        </Alert>
      )}
      {reviewMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => reviewMutation.reset()}>
          {reviewMutation.error?.message || 'Review failed.'}
        </Alert>
      )}
    </Box>
  );
}
