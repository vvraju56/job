/// Mirrors the backend `CompanyOut` schema.
class Company {
  const Company({
    required this.id,
    required this.name,
    required this.slug,
    this.logo,
    this.website,
    this.industry,
    this.description,
    this.location,
    this.size,
    this.rating,
    this.reviewCount = 0,
    this.verified = false,
    this.openPositions = 0,
  });

  final String id;
  final String name;
  final String slug;
  final String? logo;
  final String? website;
  final String? industry;
  final String? description;
  final String? location;
  final String? size;
  final double? rating;
  final int reviewCount;
  final bool verified;
  final int openPositions;

  factory Company.fromJson(Map<String, dynamic> json) {
    String? str(String key) {
      final v = json[key];
      return v == null ? null : v.toString();
    }

    int intV(String key) {
      final v = json[key];
      if (v is num) return v.toInt();
      return int.tryParse(v?.toString() ?? '') ?? 0;
    }

    double? numV(String key) {
      final v = json[key];
      if (v is num) return v.toDouble();
      return double.tryParse(v?.toString() ?? '');
    }

    bool boolV(String key) {
      final v = json[key];
      if (v is bool) return v;
      return v?.toString().toLowerCase() == 'true';
    }

    return Company(
      id: json['id'].toString(),
      name: str('name') ?? 'Unknown company',
      slug: str('slug') ?? '',
      logo: str('logo'),
      website: str('website'),
      industry: str('industry'),
      description: str('description'),
      location: str('location'),
      size: str('size'),
      rating: numV('rating'),
      reviewCount: intV('review_count'),
      verified: boolV('verified'),
      openPositions: intV('open_positions'),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'slug': slug,
        'logo': logo,
        'website': website,
        'industry': industry,
        'description': description,
        'location': location,
        'size': size,
        'rating': rating,
        'review_count': reviewCount,
        'verified': verified,
        'open_positions': openPositions,
      };
}