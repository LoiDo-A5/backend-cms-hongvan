def update_artwork_is_public_to_true(ArtWork, Collection=None, Exhibition=None):
    """
    Migration utility to update all artwork, collection and exhibition records 
    where is_public=False to is_public=True
    """
    total_updated = 0
    
    # Update ArtWork records
    artworks_to_update = ArtWork.objects.filter(is_public=False)
    artwork_count = artworks_to_update.count()
    
    if artwork_count > 0:
        updated_count = artworks_to_update.update(is_public=True)
        print(f"Updated {updated_count} artwork records: is_public=False -> is_public=True")
        total_updated += updated_count
    else:
        print("No artwork records found with is_public=False")
    
    # Update Collection records if Collection model is provided
    if Collection:
        collections_to_update = Collection.objects.filter(is_public=False)
        collection_count = collections_to_update.count()
        
        if collection_count > 0:
            updated_count = collections_to_update.update(is_public=True)
            print(f"Updated {updated_count} collection records: is_public=False -> is_public=True")
            total_updated += updated_count
        else:
            print("No collection records found with is_public=False")
    
    # Update Exhibition records if Exhibition model is provided
    if Exhibition:
        exhibitions_to_update = Exhibition.objects.filter(is_public=False)
        exhibition_count = exhibitions_to_update.count()
        
        if exhibition_count > 0:
            updated_count = exhibitions_to_update.update(is_public=True)
            print(f"Updated {updated_count} exhibition records: is_public=False -> is_public=True")
            total_updated += updated_count
        else:
            print("No exhibition records found with is_public=False")
    
    print(f"Total records updated: {total_updated}")
    return total_updated 