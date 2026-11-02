<?php

use App\Http\Controllers\ReturnsController;
use App\ReturnsSync\ReturnsSyncController;
use Illuminate\Support\Facades\Route;

Route::get('/returns', [ReturnsController::class, 'index'])->name('returns.index');

Route::get('/returns/{id}', [ReturnsController::class, 'show']);

Route::get('/returns/{id}/approve', [ReturnsController::class, 'approve'])->name('returns.approve');

Route::get('/returns/export', [ReturnsController::class, 'export'])->name('returns.export');

Route::post('/returns/{id}/reject', [ReturnsController::class, 'reject']);

Route::middleware('auth')->group(function () {
    Route::get('/returns/search', [ReturnsController::class, 'search'])->name('returns.search');
});

Route::get('/returns-sync', [ReturnsSyncController::class, 'index'])->name('returns-sync.index');

Route::get('/returns-sync/sync-now', [ReturnsSyncController::class, 'syncNow'])->name('returns-sync.sync-now');

Route::post('/returns-sync/mark-synced', [ReturnsSyncController::class, 'markSynced'])->name('returns-sync.mark-synced');
