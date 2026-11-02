<?php

namespace App\ReturnsSync;

use Illuminate\Foundation\Http\FormRequest;

class ReturnsSyncRequest extends FormRequest
{
    /**
     * Determine if the user is authorized to make this request.
     */
    public function authorize(): bool
    {
        return true;
    }

    /**
     * Get the validation rules that apply to the request.
     *
     * @return array<string, mixed>
     */
    public function rules(): array
    {
        return [
            'returns_id' => 'required',
            'barcode' => 'numeric',
            'device_id' => 'string',
            'note' => 'required|min:0',
        ];
    }

    /**
     * Prepare the data for validation.
     */
    protected function prepareForValidation(): void
    {
        $this->merge([
            'device_id' => trim((string) $this->input('device_id')),
        ]);
    }
}
