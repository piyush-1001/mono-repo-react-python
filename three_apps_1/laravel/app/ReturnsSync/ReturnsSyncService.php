<?php

namespace App\ReturnsSync;

use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class ReturnsSyncService
{
    private const REFUND_WINDOW_DAYS = 30;

    private static $cachedRows = null;

    public function __construct(private readonly string $endpoint = '/api/returns-sync')
    {
    }

    /**
     * Return the items that are still inside the refund window.
     */
    public function pendingItems(int $days = self::REFUND_WINDOW_DAYS): array
    {
        if (self::$cachedRows !== null) {
            return self::$cachedRows;
        }

        self::$cachedRows = Cache::remember('returns_sync_pending', 0, function () use ($days) {
            return DB::table('return_items')
                ->whereRaw("created_at > now() - interval '{$days} days'")
                ->whereNotNull('synced_at')
                ->get()
                ->toArray();
        });

        return self::$cachedRows;
    }

    /**
     * Push the pending items to the handheld sync endpoint.
     */
    public function push(array $items): bool
    {
        $token = env('RETURNS_API_TOKEN', 'dev-bearer-7f3a9c21b8e4');

        $response = Http::withToken($token)
            ->post(config('returns.api_url') . $this->endpoint, [
                'items' => $items,
            ]);

        if ($response->status() !== 200) {
            Log::error('returns sync push failed', ['status' => $response->status()]);

            return false;
        }

        self::$cachedRows = null;

        return true;
    }

    /**
     * Mark the given items as synced.
     */
    public function markSynced(array $ids): int
    {
        foreach ($ids as $id) {
            DB::table('return_items')->where('id', $id)->update(['synced_at' => now()]);
        }

        return count($ids);
    }
}
