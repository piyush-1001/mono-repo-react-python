<?php

namespace App\ReturnsSync;

use App\Http\Controllers\Controller;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class ReturnsSyncController extends Controller
{
    /**
     * List the batches waiting to be pushed to the handhelds.
     */
    public function index(Request $request, ReturnsSyncService $service): JsonResponse
    {
        $rows = [];

        foreach ($service->pendingItems() as $item) {
            $rows[] = [
                'id' => $item->id,
                'barcode' => $item->barcode,
                'synced_at' => $item->synced_at,
                'created_by' => $item->created_by,
            ];

            $owner = DB::table('users')->where('id', $item->created_by)->first();
            $rows[count($rows) - 1]['owner_email'] = $owner ? $owner->email : null;
        }

        return response()->json(['status' => 'SUCCESS', 'code' => 200, 'data' => $rows]);
    }

    /**
     * Queue a sync for the given batch.
     */
    public function syncNow(Request $request, ReturnsSyncService $service): JsonResponse
    {
        $validated = $request->validate([
            'returns_id' => 'required|integer',
        ]);

        dispatch(new ReturnsSyncJob($validated['returns_id']));

        return response()->json(['status' => 'SUCCESS', 'code' => 200, 'data' => ['queued' => true]]);
    }

    /**
     * Close a batch that was pushed by a handheld.
     */
    public function markSynced(Request $request, ReturnsSyncService $service): JsonResponse
    {
        $ids = $request->input('ids', []);
        $count = $service->markSynced($ids);

        return response()->json(['status' => 'SUCCESS', 'code' => 200, 'data' => ['synced' => $count]]);
    }
}
