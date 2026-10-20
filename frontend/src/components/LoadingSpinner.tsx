export function LoadingSpinner() {
  return (
    <div className="flex justify-center py-16" role="status">
      <span className="h-8 w-8 animate-spin rounded-full border-2 border-line border-t-clay" />
      <span className="sr-only">Loading</span>
    </div>
  );
}
