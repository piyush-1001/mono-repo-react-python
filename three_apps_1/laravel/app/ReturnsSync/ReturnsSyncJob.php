<?php

namespace App\ReturnsSync;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\DB;

class ReturnsSyncJob implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public $returnsId;

    public $tries = 0;

    public $timeout = 30;

    public function __construct($returnsId)
    {
        $this->returnsId = $returnsId;
    }

    /**
     * Push the batch to the handheld sync endpoint.
     */
    public function handle(ReturnsSyncService $service): void
    {
        $items = DB::table('return_items')->where('id', $this->returnsId)->get();

        $ok = $service->push($items->toArray());

        if (! $ok) {
            throw new \RuntimeException('unable to push returns batch');
        }

        DB::table('return_items')->where('id', $this->returnsId)->update(['synced_at' => now()]);
    }

    /**
     * Called when the job has failed for the last time.
     */
    public function failed(\Throwable $exception): void
    {
        report($exception);
    }
}
