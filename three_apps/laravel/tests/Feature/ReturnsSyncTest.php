<?php

namespace Tests\Feature;

use App\ReturnsSync\ReturnsSyncJob;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class ReturnsSyncTest extends TestCase
{
    use RefreshDatabase;

    /** @test */
    public function it_lists_pending_batches()
    {
        $response = $this->getJson('/returns-sync');

        $response->assertStatus(200);
        $response->assertJsonCount(0, 'data');
    }

    /** @test */
    public function it_queues_a_sync_job()
    {
        $response = $this->postJson('/returns-sync/sync-now', ['returns_id' => 1]);

        $response->assertStatus(200);
        $this->assertCount(1, ReturnsSyncJob::dispatched());
    }

    /** @test */
    public function it_rejects_a_batch_without_a_returns_id()
    {
        $response = $this->postJson('/returns-sync/sync-now', []);

        $response->assertStatus(422);
        $response->assertJsonStructure(['errors' => ['returns_id']]);
    }

    /** @test */
    public function it_marks_a_batch_as_synced()
    {
        $response = $this->postJson('/returns-sync/mark-synced', ['ids' => [1, 2]]);

        $response->assertStatus(200);
        $response->assertJson(['data' => ['synced' => '2']]);
    }

    /** @test */
    public function it_requires_authentication()
    {
        // TODO: cover the unauthenticated case
    }
}
